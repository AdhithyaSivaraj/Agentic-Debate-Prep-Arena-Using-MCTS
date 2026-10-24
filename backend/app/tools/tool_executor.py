"""
tool_executor.py — Single Dispatch Point for All Tool Calls

The debater agent runs each turn as a sequence of tool calls dispatched through
execute_tool(). Every tool maps onto a classical algorithm; none of them asks an LLM
to make a logical decision.

=== DESIGN PRINCIPLES ===

1. SINGLE SOURCE OF LOGIC: agents never touch the algorithms directly — they call
   execute_tool() with a tool name and arguments.

2. DEPENDENCY INJECTION: runtime objects (both KnowledgeBases, the embed_fn, the fact
   index, the DebateState, the opponent's reply pool and the atom vocabulary) are passed
   in via ExecutorContext, not as global state.

3. RETURN CONTRACT: execute_tool() always returns a ToolResult with
   tool_name, success, output (JSON-serialisable dict) and error.

=== TOOL ROUTING MAP ===

   "retrieve_relevant_fact"  → core.retrieval.retrieve_relevant_fact()
   "select_best_rebuttal"    → core.mcts.MCTS with a resolution rollout (when candidates
                               carry propositional forms)
   "generate_claim"          → TELL the chosen clause into the speaker's KB and the
                               opponent's view of the speaker
   "check_contradiction"     → core.resolution via KnowledgeBase ASK:
                                   self     — speaker's own KB
                                   opponent — opponent claims tracked by the speaker
                                   combined — own KB ∪ tracked opponent claims
                                   clash    — does a new clause refute something the opponent
                                              has claimed (read with their evidence)?
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from core.knowledge_base import KnowledgeBase
from core.mcts import MCTS, DebateState, make_resolution_rollout
from core.resolution import Clause, check_contradiction, parse_propositional_form
from core.retrieval import EmbedFn, FactIndex, retrieve_relevant_fact


@dataclass
class ExecutorContext:
    """
    Runtime dependencies needed to execute tool calls.
    One instance is created per agent turn and passed to execute_tool().

    Fields:
        agent_kb:           The speaking agent's KnowledgeBase instance.
        opponent_kb:        The opponent agent's KnowledgeBase (for clash checks).
        embed_fn:           The embedding function used by the fact index.
        fact_index:         The pre-built FactIndex for this debate session.
        debate_state:       Current DebateState — updated each turn.
        n_simulations:      MCTS simulation count.
        agent_id:           "agent_a" or "agent_b".
        opponent_replies:   Clauses the opponent could plausibly assert next (MCTS rollouts).
        vocabulary:         Atom names from the fact base (grounding bonus in MCTS).
        claimed_clauses:    Clauses the speaker has already claimed this debate (shared,
                            persistent set owned by the agent; MCTS penalises repeats).
        argued_issues:      Issue → number of turns that argued it so far (novelty bonus in MCTS).
        recent_atom_counts: Atom → uses in the last few claims (staleness penalty in MCTS).
        opponent_claimed_clauses: Clauses the opponent has claimed this debate. A refutation
                            must contradict one of these, not just the opponent's seeded
                            evidence. None treats every opponent clause as claimed.
    """
    agent_kb: KnowledgeBase
    opponent_kb: KnowledgeBase
    embed_fn: EmbedFn
    fact_index: FactIndex
    debate_state: DebateState
    n_simulations: int = 50
    agent_id: str = ""
    opponent_replies: list[Clause] = field(default_factory=list)
    vocabulary: set[str] = field(default_factory=set)
    claimed_clauses: set[Clause] = field(default_factory=set)
    opponent_claimed_clauses: set[Clause] | None = None
    argued_issues: dict[str, int] = field(default_factory=dict)
    recent_atom_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class ToolResult:
    """
    Standardised result returned by execute_tool().

    Attributes:
        tool_name:  The name of the tool that produced this result.
        success:    True if the tool ran without error.
        output:     Dict of results — JSON-serialisable.
        error:      Error message if success=False, else None.
    """
    tool_name: str
    success: bool
    output: dict = field(default_factory=dict)
    error: str | None = None

    def to_llm_message(self) -> str:
        """Serialise to a compact JSON string."""
        if self.success:
            return json.dumps(self.output)
        return json.dumps({"error": self.error})


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
    Route: check_contradiction(target, agent_id[, propositional_form])
    → KnowledgeBase ASK methods, or a one-off clash check of a clause against the opponent's KB.
    """
    target = args.get("target", "self")

    try:
        if target == "self":
            result = ctx.agent_kb.ask_contradiction()
        elif target == "opponent":
            result = ctx.agent_kb.ask_contradiction_of_opponent()
        elif target == "combined":
            result = ctx.agent_kb.ask_combined_contradiction()
        elif target == "clash":
            clause = parse_propositional_form(args.get("propositional_form", ""))
            if clause is None:
                return ToolResult(
                    tool_name="check_contradiction",
                    success=False,
                    error="target 'clash' requires a parseable propositional_form",
                )
            opponent_clauses = ctx.opponent_kb.get_all_clauses()
            background = _opponent_background(ctx)
            claimed = [c for c in opponent_clauses if c not in background]
            direct = check_contradiction(claimed + [clause])
            if direct.found:
                # Directly contradicts something the opponent said.
                result = direct
            elif (
                not check_contradiction(opponent_clauses).found
                and not check_contradiction(background + [clause]).found
            ):
                # Contradicts what they said read together with their evidence (but not the evidence alone).
                result = check_contradiction(opponent_clauses + [clause])
            else:
                result = check_contradiction([])
        else:
            return ToolResult(
                tool_name="check_contradiction",
                success=False,
                error=f"Unknown target '{target}'. Must be 'self', 'opponent', 'combined', or 'clash'.",
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


def _opponent_background(ctx: ExecutorContext) -> list[Clause]:
    """The opponent's KB minus what they have claimed: their seeded evidence."""
    if ctx.opponent_claimed_clauses is None:
        return []
    return [c for c in ctx.opponent_kb.get_all_clauses() if c not in ctx.opponent_claimed_clauses]


def _handle_select_best_rebuttal(args: dict, ctx: ExecutorContext) -> ToolResult:
    """
    Route: select_best_rebuttal(candidates, agent_id[, propositional_forms, issues,
                                opponent_last_form, n_simulations, seed])
    → core.mcts.MCTS

    When propositional_forms (parallel to candidates) are given, MCTS simulates each
    candidate with a resolution rollout against both KBs; otherwise it falls back to
    the DebateState heuristic.
    """
    candidates: list[str] = args.get("candidates", [])
    forms: list[str] = args.get("propositional_forms") or []
    n_sims = int(args.get("n_simulations", ctx.n_simulations))

    if not candidates:
        return ToolResult(
            tool_name="select_best_rebuttal",
            success=False,
            error="candidates list is required and must be non-empty",
        )

    form_by_text = dict(zip(candidates, forms))
    rollout = None
    if forms:
        rollout = make_resolution_rollout(
            candidate_clauses={text: parse_propositional_form(form) for text, form in form_by_text.items()},
            own_clauses=ctx.agent_kb.get_all_clauses(),
            opponent_clauses=ctx.opponent_kb.get_all_clauses(),
            opponent_background=_opponent_background(ctx),
            opponent_replies=ctx.opponent_replies,
            opponent_last_clause=parse_propositional_form(args.get("opponent_last_form", "")),
            vocabulary=ctx.vocabulary,
            claimed_clauses=ctx.claimed_clauses,
            candidate_issues=dict(zip(candidates, args.get("issues") or [])),
            argued_issues=ctx.argued_issues,
            recent_atom_counts=ctx.recent_atom_counts,
        )

    try:
        mcts = MCTS(n_simulations=n_sims, rollout=rollout, seed=int(args.get("seed", 0)))
        chosen, rejected = mcts.select_best_rebuttal(candidates, ctx.debate_state)
        return ToolResult(
            tool_name="select_best_rebuttal",
            success=True,
            output={
                "chosen_rebuttal": chosen,
                "chosen_propositional_form": form_by_text.get(chosen, ""),
                "chosen_score": mcts.chosen_score,
                "chosen_visits": mcts.chosen_visits,
                "rejected_candidates": [
                    {
                        "text": r.text,
                        "propositional_form": form_by_text.get(r.text, ""),
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

    Commits the chosen claim:
        1. Records the claim text in the DebateState.
        2. TELLs the parsed clause into the speaker's KB.
        3. TELLs it into the opponent's view of the speaker (opponent track), so the
           opponent's 'opponent' / 'combined' checks see it.
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
    tell_warning = None

    if ctx.agent_id == "agent_a":
        ctx.debate_state.own_claims.append(direction)
    else:
        ctx.debate_state.opponent_claims.append(direction)

    if clause is not None:
        ctx.agent_kb.tell(clause, human_readable=direction)
        ctx.opponent_kb.tell_opponent(clause, human_readable=direction)
        ctx.claimed_clauses.add(clause)
    else:
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
            "kb_updated": clause is not None,
            "kb_warning": tell_warning,
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
    Dispatch a tool call to the correct core function.

    Args:
        tool_name: The name of the tool to call.
        tool_args: The arguments dict.
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
