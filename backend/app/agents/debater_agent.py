"""
debater_agent.py — The debater agent (one class for every LLM provider).

Each turn is a fixed agentic loop over tool calls (tool_executor.py):

    1. retrieve_relevant_fact   — evidence relevant to the opponent's last claim (Unit II)
    2. LLM plans, then proposes — reads the exchange so far, decides what is contested,
                                  and writes candidates that either rebut or open a new
                                  issue, each with a propositional form in the shared vocabulary
    3. select_best_rebuttal     — MCTS scores candidates with resolution rollouts (Unit III)
    4. generate_claim           — TELL the chosen clause into both knowledge bases (Unit IV)
    5. check_contradiction      — did the claim contradict ourselves? does it clash
                                  with the opponent's position? (Unit IV)

The LLM only writes language. Which candidate is spoken is decided by MCTS, and
contradictions are decided by resolution. If the LLM is unavailable, candidates come
from the agent's side of the generated fact base and the turn is marked "fallback".
"""
from __future__ import annotations

import logging
from typing import Any

from core.fact_generation import DebateFrame, FactRecord
from core.knowledge_base import KnowledgeBase
from core.resolution import atoms_of, clause_to_str, parse_propositional_form
from llm_client import (
    LLMUnavailable,
    clean_claim_text,
    complete_with_fallbacks,
    humanize_logic,
    parse_json_payload,
    provider_for,
)
from tools.tool_executor import ExecutorContext, execute_tool

logger = logging.getLogger(__name__)

N_CANDIDATES = 4
EMPTY_RESULT = {"found": False, "conflicting_clauses": [], "proof_steps": []}

CANDIDATE_SYSTEM_PROMPT = (
    "You are a skilled competitive debater. Think about what is actually contested before you write. "
    "You propose candidate arguments; a separate search algorithm checks their logic and picks one. "
    "Output JSON only."
)


def side_facts(facts: list[FactRecord], role: str) -> list[FactRecord]:
    """Facts on a role's side of the resolution (independent facts belong to both sides)."""
    own = "supports_proposition" if role == "proposer" else "contradicts_proposition"
    return [f for f in facts if f.relationship in (own, "is_independent")]


class DebaterAgent:
    """A debater with a private knowledge base, an LLM for phrasing, and a side of the fact base."""

    def __init__(self, agent_id: str, role: str, model_name: str, facts: list[FactRecord], frame: DebateFrame):
        self.agent_id = agent_id
        self.role = role
        self.model_name = model_name
        self.facts = facts
        self.frame = frame
        self.side_facts = side_facts(facts, role)
        self.kb = KnowledgeBase(agent_id)
        self.claimed_clauses: set = set()

    @property
    def position(self) -> str:
        return self.frame.proposer_position if self.role == "proposer" else self.frame.opponent_position

    @property
    def opposing_position(self) -> str:
        return self.frame.opponent_position if self.role == "proposer" else self.frame.proposer_position

    def run_turn(
        self,
        topic: str,
        opponent_last_claim: str | None,
        opponent_last_form: str | None,
        turn_number: int,
        ctx: ExecutorContext,
        history: list[str] | None = None,
    ) -> dict[str, Any]:
        ctx.agent_id = self.agent_id
        ctx.claimed_clauses = self.claimed_clauses
        spoken = ctx.debate_state.own_claims if self.agent_id == "agent_a" else ctx.debate_state.opponent_claims

        fact_res = execute_tool(
            "retrieve_relevant_fact",
            {"claim_topic": opponent_last_claim or self.position, "top_k": 5},
            ctx,
        )
        evidence = fact_res.output.get("retrieved_facts", []) if fact_res.success else []

        mode, model_used = "live", None
        try:
            candidates, model_used = self._propose_candidates(
                topic, opponent_last_claim, opponent_last_form, spoken, evidence, ctx, history or []
            )
        except (LLMUnavailable, ValueError) as e:
            logger.warning(f"{self.agent_id}: candidate generation failed ({str(e)[:200]}). Using fact-base candidates.")
            candidates, mode = self._fallback_candidates(spoken), "fallback"

        texts = [c["claim"] for c in candidates]
        mcts_res = execute_tool(
            "select_best_rebuttal",
            {
                "candidates": texts,
                "propositional_forms": [c["propositional"] for c in candidates],
                "issues": [c.get("issue", "") for c in candidates],
                "opponent_last_form": opponent_last_form or "",
                "agent_id": self.agent_id,
                "seed": turn_number,
            },
            ctx,
        )
        mcts_trace = mcts_res.output if mcts_res.success else None
        claim_text = mcts_trace["chosen_rebuttal"] if mcts_trace else texts[0]
        chosen = next(c for c in candidates if c["claim"] == claim_text)
        prop_form = chosen["propositional"]

        chosen_clause = parse_propositional_form(prop_form)
        is_repeat = chosen_clause in self.claimed_clauses
        self_before = execute_tool("check_contradiction", {"target": "self"}, ctx)
        execute_tool(
            "generate_claim",
            {
                "context": f"Topic: {topic}. Role: {self.role}.",
                "direction": claim_text,
                "propositional_form": prop_form,
                "agent_id": self.agent_id,
            },
            ctx,
        )
        self_after = execute_tool("check_contradiction", {"target": "self"}, ctx)
        new_self_contradiction = (
            self_after.success and self_after.output["found"]
            and not (self_before.success and self_before.output["found"])
        )
        if new_self_contradiction and chosen_clause is not None:
            # Scored and shown, then withdrawn so this agent's commitments stay consistent and refutable.
            ctx.agent_kb.retract(chosen_clause)
            ctx.opponent_kb.retract_opponent(chosen_clause)
        clash = execute_tool("check_contradiction", {"target": "clash", "propositional_form": prop_form}, ctx)

        return {
            "speaker": self.agent_id,
            "turn_number": turn_number,
            "claim_text": claim_text,
            "propositional_form": prop_form,
            "issue": chosen.get("issue", ""),
            "contradiction_result": self_after.output if new_self_contradiction else EMPTY_RESULT,
            # Re-asserting a position already held is not a new refutation.
            "clash_result": clash.output if clash.success and not is_repeat else EMPTY_RESULT,
            "mcts_trace": mcts_trace,
            "mode": mode,
            "model_used": model_used,
        }

    def _propose_candidates(
        self,
        topic: str,
        opponent_last_claim: str | None,
        opponent_last_form: str | None,
        spoken: list[str],
        evidence: list[dict],
        ctx: ExecutorContext,
        history: list[str],
    ) -> tuple[list[dict[str, str]], str]:
        """Ask the LLM to plan and propose candidates; keep on-side ones with a parseable form."""
        if opponent_last_claim:
            last = f'"{opponent_last_claim}"' + (f" (logical form: {opponent_last_form})" if opponent_last_form else "")
        else:
            last = "None — you give the opening statement. Lead with your single strongest reason."
        exchange = "\n".join(history[-8:]) or "(no turns yet)"
        argued = ", ".join(f"{k} ×{v}" for k, v in sorted(ctx.argued_issues.items(), key=lambda kv: -kv[1])) or "(none yet)"
        evidence_lines = "\n".join(f"- {e['text']}  [{self._form_of_fact(e['text'])}]" for e in evidence) or "- (none)"
        vocabulary = sorted(
            {a for c in ctx.agent_kb.get_all_clauses() + ctx.opponent_kb.get_all_clauses() for a in atoms_of(c)}
        )
        opponent_positions = ", ".join(clause_to_str(c) for c in ctx.opponent_kb.get_all_clauses()[-12:]) or "(none)"
        own_label = "Proposer" if self.role == "proposer" else "Opponent"

        prompt = f"""Debate topic: "{topic}"
Resolution: "{self.frame.resolution}"
YOU are the {own_label}. Your position: {self.position}
The other side's position: {self.opposing_position}
Every argument you write must help YOUR position. Never concede the other side's point or argue for their option.

The exchange so far (most recent last):
{exchange}

Opponent's last claim: {last}
Issues argued so far: {argued}

Evidence from the fact base (with logical forms):
{evidence_lines}

Logical vocabulary (atoms in play): {", ".join(vocabulary) or "(none)"}
Opponent's committed positions (as clauses): {opponent_positions}

First, think like a debater and write a short "plan" (2-3 sentences): what is the opponent really
relying on, is it worth rebutting, and which issue that matters to the decision has not been argued
enough? Then write {N_CANDIDATES} distinct candidate arguments:
- 1–2 candidates REBUT the opponent's last claim (attack its premise or its consequence)
- the rest ADVANCE your case on a different issue — prefer issues not argued yet (cost, performance,
  reliability, practicality, long-term value, …) over re-arguing one that has been argued 3+ times
- 2–3 sentences each, as you would say them aloud, with a concrete fact, number or example
- plain English only; no filler, no restating the resolution, no talk about the debate itself
  ("your claim", "as I said"); never repeat or reword one of your earlier arguments
- "propositional": the claim's core logical content as "A", "¬A" or "A → B", reusing vocabulary
  atoms where they fit. Atom names must name their subject (GamingLaptopHeavy, not WeightHeavy).
  A claim that denies one of the opponent's committed positions is verified as a refutation.
- "issue": one or two words naming the issue (e.g. "cost", "battery life")
- "helps": which side this argument helps — must be "{self.role}"

Return {{"plan": "...", "candidates": [{{"claim": "...", "propositional": "...", "issue": "...", "helps": "{self.role}"}}]}}"""

        provider = provider_for(self.model_name)[0]
        raw, model_used = complete_with_fallbacks(
            self.model_name,
            CANDIDATE_SYSTEM_PROMPT,
            prompt,
            json_mode=provider in ("groq", "gemini"),
            temperature=0.7,
            timeout=45.0,
            reasoning_effort="medium",
        )
        data = parse_json_payload(raw)
        items = data.get("candidates", []) if isinstance(data, dict) else data
        candidates: list[dict[str, str]] = []
        seen = {s.strip().lower() for s in spoken}
        seen_clauses = set()
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            if str(item.get("helps", self.role)).strip().lower() not in (self.role, ""):
                continue  # argues for the other side
            claim = humanize_logic(clean_claim_text(str(item.get("claim", ""))), set(vocabulary))
            form = str(item.get("propositional", "")).strip()
            clause = parse_propositional_form(form)
            if claim and claim.lower() not in seen and clause is not None and clause not in seen_clauses:
                candidates.append({"claim": claim, "propositional": form, "issue": str(item.get("issue", "")).strip().lower()})
                seen.add(claim.lower())
                seen_clauses.add(clause)
        if not candidates:
            raise ValueError(f"No usable candidates in response from '{model_used}'.")
        return candidates, model_used

    def _fallback_candidates(self, spoken: list[str]) -> list[dict[str, str]]:
        """Unspoken facts from this agent's side of the fact base, as ready-made claims."""
        usable = [f for f in self.side_facts if f.clause is not None] or [f for f in self.facts if f.clause is not None]
        fresh = [f for f in usable if f.text not in spoken] or usable
        return [{"claim": f.text, "propositional": f.propositional, "issue": ""} for f in fresh[:N_CANDIDATES + 1]]

    def _form_of_fact(self, text: str) -> str:
        for fact in self.facts:
            if fact.text == text:
                return fact.propositional
        return "?"
