"""
tool_executor.py — Single Dispatch Point for All Tool Calls

This module is the bridge between the LLM's function-calling output and the
core algorithm implementations. When either GeminiAgent or NemotronAgent receives
a tool_call from its respective LLM, it hands the call to execute_tool() here.

=== DESIGN PRINCIPLES ===

1. SINGLE SOURCE OF LOGIC: Both agents call execute_tool() with the same arguments.
   There is NO tool logic duplicated in gemini_agent.py or nemotron_agent.py —
   only LLM-specific API call code lives there.

2. DEPENDENCY INJECTION: The executor needs access to runtime objects that don't
   exist at import time — the agent's KnowledgeBase, the embed_fn, the MCTS
   n_simulations setting, and the DebateState. These are passed in via
   ExecutorContext (a dataclass), not as global state.

3. RETURN CONTRACT: execute_tool() always returns a ToolResult dataclass with:
   - tool_name:   the name of the tool that was called
   - success:     bool
   - output:      the serialisable result (dict) to hand back to the LLM
   - error:       error message string if success=False, else None

   The LLM receives output as a "tool result" message in its conversation context.
   The agent loop code also reads specific fields (e.g., output["found"]) to
   decide whether to call select_best_rebuttal next.

=== TOOL ROUTING MAP ===

   "retrieve_relevant_fact"  → core.retrieval.retrieve_relevant_fact()
   "check_contradiction"     → KnowledgeBase.ask_contradiction() / ask_contradiction_of_opponent() / ask_combined_contradiction()
   "select_best_rebuttal"    → core.mcts.select_best_rebuttal()
   "generate_claim"          → LLM call (handled by the agent; executor records the claim into KB)

=== NOTE ON generate_claim ===

generate_claim is special: the LLM IS the implementation (it's the only tool where
the LLM freely generates language). The executor does not route it to a core function.
Instead, when generate_claim is called, the executor:
    1. Records the propositional_form into the agent's KB via TELL.
    2. Returns the claim context back to the agent so it can feed it into the LLM
       as the actual generation prompt.

The agent's LLM then produces the fluent natural-language text for the claim.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.resolution import (
    Clause,
    atom,
    neg_atom,
    implication_to_clause,
    clause_to_str,
)
from core.knowledge_base import KnowledgeBase
from core.retrieval import retrieve_relevant_fact, EmbedFn, FactIndex
from core.mcts import select_best_rebuttal, DebateState, RejectedCandidate


@dataclass
class ExecutorContext:
    """
    Runtime dependencies needed to execute tool calls.
    One instance is created per agent per debate session and passed to execute_tool().

    Fields:
        agent_kb:           The owning agent's KnowledgeBase instance.
        opponent_kb:        The opponent agent's KnowledgeBase (for cross-KB checks).
        embed_fn:           The embedding function (Nemotron 3 Embed 1B in production,
                            fake function in tests).
        fact_index:         The pre-built FactIndex for this debate session.
        debate_state:       Current DebateState — updated each turn, used by MCTS.
        n_simulations:      MCTS simulation count (default from config).
        agent_id:           "agent_a" or "agent_b" — for KB lookup.
    """
    agent_kb: KnowledgeBase
    opponent_kb: KnowledgeBase
    embed_fn: EmbedFn
    fact_index: FactIndex
    debate_state: DebateState
    n_simulations: int = 50
    agent_id: str = ""
    turn_history: list[str] = field(default_factory=list)


@dataclass
class ToolResult:
    """
    Standardised result returned by execute_tool().

    Attributes:
        tool_name:  The name of the tool that produced this result.
        success:    True if the tool ran without error.
        output:     Dict of results — serialisable to JSON for the LLM's tool-result message.
        error:      Error message if success=False, else None.
    """
    tool_name: str
    success: bool
    output: dict = field(default_factory=dict)
    error: str | None = None

    def to_llm_message(self) -> str:
        """
        Serialise to a compact string suitable for injection as a tool-result message
        into the LLM's conversation context.

        The LLM sees this after calling a tool — it reads the result and decides
        what to do next (call another tool, or generate a claim).
        """
        import json
        if self.success:
            return json.dumps(self.output)
        return json.dumps({"error": self.error})


def parse_propositional_form(prop_form: str) -> Clause | None:
    """
    Parse a propositional form string into a Clause (frozenset of literals).

    Supported formats:
        "A → B"    →  implication_to_clause("A", "B")   →  frozenset({("NOT","A"), "B"})
        "A"        →  atom("A")                          →  frozenset({"A"})
        "¬A"       →  neg_atom("A")                      →  frozenset({("NOT","A")})
        "NOT A"    →  neg_atom("A")                      →  frozenset({("NOT","A")})

    Returns None if the string cannot be parsed (caller should log a warning and skip).

    Note: atom names must be single CamelCase tokens (no spaces within the name).
    """
    prop_form = prop_form.strip()

                                      
    for sep in ["→", "->"]:
        if sep in prop_form:
            parts = prop_form.split(sep, 1)
            antecedent = parts[0].strip()
            consequent = parts[1].strip()
            if antecedent and consequent:
                return implication_to_clause(antecedent, consequent)

                               
    if prop_form.startswith("¬"):
        atom_name = prop_form[1:].strip()
        if atom_name:
            return neg_atom(atom_name)

    if prop_form.upper().startswith("NOT "):
        atom_name = prop_form[4:].strip()
        if atom_name:
            return neg_atom(atom_name)

                           
    if prop_form and " " not in prop_form:
        return atom(prop_form)

    return None                    


def _handle_retrieve_relevant_fact(args: dict, ctx: ExecutorContext) -> ToolResult:
    """
    Route: retrieve_relevant_fact(claim_topic, top_k=1)
    → core.retrieval.retrieve_relevant_fact()
    """
    claim_topic = args.get("claim_topic", "")
    top_k = int(args.get("top_k", 1))

    if not claim_topic:
        return ToolResult(
            tool_name="retrieve_relevant_fact",
            success=False,
            error="claim_topic is required",
        )

    try:
        results = retrieve_relevant_fact(
            query=claim_topic,
            embed_fn=ctx.embed_fn,
            top_k=top_k,
            index=ctx.fact_index,
        )
        return ToolResult(
            tool_name="retrieve_relevant_fact",
            success=True,
            output={
                "retrieved_facts": [
                    {"text": r.text, "score": r.score, "index": r.index}
                    for r in results
                ],
                "top_fact": results[0].text if results else "",
            },
        )
    except Exception as e:
        return ToolResult(
            tool_name="retrieve_relevant_fact",
            success=False,
            error=str(e),
        )


def _handle_check_contradiction(args: dict, ctx: ExecutorContext) -> ToolResult:
    """
    Route: check_contradiction(target, agent_id)
    → KnowledgeBase.ask_contradiction() / ask_contradiction_of_opponent() / ask_combined_contradiction()
    """
    target = args.get("target", "self")                                     

    try:
        if target == "self":
            result = ctx.agent_kb.ask_contradiction()
        elif target == "opponent":
            result = ctx.agent_kb.ask_contradiction_of_opponent()
        elif target == "combined":
            result = ctx.agent_kb.ask_combined_contradiction()
        else:
            return ToolResult(
                tool_name="check_contradiction",
                success=False,
                error=f"Unknown target '{target}'. Must be 'self', 'opponent', or 'combined'.",
            )

        return ToolResult(
            tool_name="check_contradiction",
            success=True,
            output={
                "found": result.found,
                "conflicting_clauses": result.conflicting_clauses,
                "proof_steps": result.proof_steps,
                "summary": (
                    f"Contradiction detected in {target} KB: "
                    + (result.conflicting_clauses[0][0] if result.conflicting_clauses else "")
                    if result.found
                    else f"No contradiction found in {target} KB."
                ),
            },
        )
    except Exception as e:
        return ToolResult(
            tool_name="check_contradiction",
            success=False,
            error=str(e),
        )


def _handle_select_best_rebuttal(args: dict, ctx: ExecutorContext) -> ToolResult:
    """
    Route: select_best_rebuttal(candidates, agent_id, n_simulations=50)
    → core.mcts.select_best_rebuttal()
    """
    candidates: list[str] = args.get("candidates", [])
    n_sims = int(args.get("n_simulations", ctx.n_simulations))

    if not candidates:
        return ToolResult(
            tool_name="select_best_rebuttal",
            success=False,
            error="candidates list is required and must be non-empty",
        )

    if len(candidates) == 1:
                                                                                    
        pass

    try:
        chosen, rejected = select_best_rebuttal(
            candidates=candidates,
            current_state=ctx.debate_state,
            n_simulations=n_sims,
        )
        return ToolResult(
            tool_name="select_best_rebuttal",
            success=True,
            output={
                "chosen_rebuttal": chosen,
                "rejected_candidates": [
                    {
                        "text": r.text,
                        "score": r.score,
                        "visit_count": r.visit_count,
                    }
                    for r in rejected
                ],
                "n_simulations": n_sims,
                "summary": (
                    f"MCTS selected: '{chosen}' "
                    f"(over {len(rejected)} alternatives after {n_sims} simulations)"
                ),
            },
        )
    except Exception as e:
        return ToolResult(
            tool_name="select_best_rebuttal",
            success=False,
            error=str(e),
        )


def _handle_generate_claim(args: dict, ctx: ExecutorContext) -> ToolResult:
    """
    Route: generate_claim(context, direction, propositional_form, agent_id)

    This tool is special — the LLM IS the implementation (it generates the language).
    The executor's job here is:
        1. Parse and validate the propositional_form.
        2. TELL the clause into the agent's KB.
        3. Return the context + direction back as the "output" so the agent can
           use them to construct the actual LLM generation prompt.

    The actual natural-language claim text is produced by the LLM AFTER it receives
    this tool result — the agent then injects the output into a completion call.
    """
    context = args.get("context", "")
    direction = args.get("direction", "")
    prop_form = args.get("propositional_form", "")

    if not context or not direction or not prop_form:
        return ToolResult(
            tool_name="generate_claim",
            success=False,
            error="context, direction, and propositional_form are all required",
        )

                                                          
    clause = parse_propositional_form(prop_form)
    tell_success = True
    tell_warning = None

                                                    
    if ctx.agent_id == "agent_a":
        ctx.debate_state.own_claims.append(direction)
    else:
        ctx.debate_state.opponent_claims.append(direction)

    if clause is not None:
        ctx.agent_kb.tell(clause, human_readable=direction)
    else:
        tell_success = False
        tell_warning = (
            f"Could not parse propositional form '{prop_form}' — "
            "claim added to history but not asserted into KB. "
            "Use format: 'A → B', 'A', or '¬A'."
        )

    return ToolResult(
        tool_name="generate_claim",
        success=True,                                                                
        output={
            "context": context,
            "direction": direction,
            "propositional_form": prop_form,
            "kb_updated": tell_success,
            "kb_warning": tell_warning,
            "instruction": (
                "Now generate a fluent, debate-quality natural-language argument "
                f"following this direction: '{direction}'. "
                f"Ground it in the retrieved fact from context. "
                "Be concise, logical, and directly responsive to the debate topic."
            ),
        },
    )


_TOOL_HANDLERS: dict[str, Any] = {
    "retrieve_relevant_fact": _handle_retrieve_relevant_fact,
    "check_contradiction":    _handle_check_contradiction,
    "select_best_rebuttal":   _handle_select_best_rebuttal,
    "generate_claim":         _handle_generate_claim,
}


def execute_tool(
    tool_name: str,
    tool_args: dict,
    ctx: ExecutorContext,
) -> ToolResult:
    """
    Dispatch a tool call from either LLM to the correct core function.

    Args:
        tool_name: The name of the tool to call (must match a key in TOOL_SCHEMAS).
        tool_args: The arguments dict parsed from the LLM's function-call output.
        ctx:       ExecutorContext containing runtime dependencies.

    Returns:
        ToolResult with success/failure and serialisable output.
    """
    handler = _TOOL_HANDLERS.get(tool_name)

    if handler is None:
        return ToolResult(
            tool_name=tool_name,
            success=False,
            error=(
                f"Unknown tool '{tool_name}'. "
                f"Valid tools: {list(_TOOL_HANDLERS.keys())}"
            ),
        )

    return handler(tool_args, ctx)


def get_available_tool_names() -> list[str]:
    """Return the list of all registered tool names."""
    return list(_TOOL_HANDLERS.keys())
