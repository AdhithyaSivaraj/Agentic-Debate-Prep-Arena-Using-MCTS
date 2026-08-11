"""
knowledge_base.py — KB Agent TELL/ASK Interface (Unit IV: Knowledge-Based Agents)

This implements the TELL/ASK pattern from the AIMA textbook (Russell & Norvig),
directly matching the course syllabus Unit IV architecture:

    TELL(kb, sentence)  — assert a new clause into the KB
    ASK(kb, query)      — query the KB (here: run contradiction detection)

Each debater agent holds its own private KnowledgeBase instance.
The KB accumulates clauses across turns, preserving the "persistent state" property
that makes the system agentic (not a one-shot prompt/response).

CONSTRAINT (must never be violated):
    ask_contradiction() delegates to resolution.py — it NEVER calls an LLM.
    Contradiction detection is fully deterministic and algorithmic.
"""
from __future__ import annotations

from core.resolution import (
    Clause,
    ContradictionResult,
    check_contradiction,
    clause_to_str,
)


class KnowledgeBase:
    """
    Per-agent knowledge base implementing the TELL/ASK pattern.

    Each debater agent creates one KnowledgeBase instance and holds it across
    all turns of the debate. After every claim:
        1. The agent calls `tell(clause)` to assert the claim's propositional form.
        2. The agent calls `ask_contradiction()` to check if the KB is now unsatisfiable.

    The KB also stores opponent clauses optionally — an agent may optionally call
    `tell_opponent(clause)` to track the opponent's KB separately, then call
    `ask_contradiction_of(opponent_kb)` to check if the opponent has contradicted themselves.
    """

    def __init__(self, agent_id: str):
        """
        Args:
            agent_id: Identifier for the owning agent ("agent_a" or "agent_b").
                      Used for logging and debugging — not logic-critical.
        """
        self.agent_id: str = agent_id
        self._clauses: list[Clause] = []                                               
        self._opponent_clauses: list[Clause] = []                                         
        self._history: list[str] = []                                                        

                                                                        
    def tell(self, clause: Clause, human_readable: str = "") -> None:
        """
        TELL: assert a new propositional clause into this agent's knowledge base.

        Args:
            clause:         The clause to assert (frozenset of literals from resolution.py).
            human_readable: Optional plain-English version of the claim (for UI display).
                            Stored in history but not used for reasoning.

        Duplicate clauses are silently ignored — asserting the same fact twice
        does not create a duplicate entry (set-like semantics, but order-preserving
        for proof trace readability).
        """
        if clause not in self._clauses:
            self._clauses.append(clause)
        if human_readable:
            self._history.append(human_readable)

    def tell_opponent(self, clause: Clause, human_readable: str = "") -> None:
        """
        TELL (opponent track): assert a clause attributed to the opponent.
        Stored separately so we can check if the opponent's own KB is contradictory.
        """
        if clause not in self._opponent_clauses:
            self._opponent_clauses.append(clause)
        if human_readable:
            self._history.append(f"[opponent] {human_readable}")

                                                                        
    def ask_contradiction(self) -> ContradictionResult:
        """
        ASK: run propositional resolution refutation over all clauses in this KB.

        Returns ContradictionResult with found=True if the KB is unsatisfiable
        (i.e., this agent's own claims contradict each other).

        Delegates entirely to resolution.check_contradiction() — never calls an LLM.
        """
        return check_contradiction(self._clauses)

    def ask_contradiction_of_opponent(self) -> ContradictionResult:
        """
        ASK: run contradiction detection over the opponent's tracked clauses.
        Used by an agent to check if the opponent has contradicted themselves.
        """
        return check_contradiction(self._opponent_clauses)

    def ask_combined_contradiction(self) -> ContradictionResult:
        """
        ASK: run contradiction detection over the combined KB (own + opponent).
        Used to check for cross-agent logical conflicts — i.e., whether this agent's
        claims directly contradict the opponent's claims.
        """
        combined = self._clauses + self._opponent_clauses
        return check_contradiction(combined)

                                                                        
    def get_all_clauses(self) -> list[Clause]:
        """Return a snapshot of all own clauses currently in the KB."""
        return list(self._clauses)

    def get_opponent_clauses(self) -> list[Clause]:
        """Return a snapshot of all tracked opponent clauses."""
        return list(self._opponent_clauses)

    def get_history(self) -> list[str]:
        """Return the human-readable claim history (for UI transcript panel)."""
        return list(self._history)

    def summary(self) -> dict:
        """
        Return a compact summary dict suitable for serialising to the API response
        (used by the /next-turn endpoint to include KB status in the Turn object).
        """
        return {
            "agent_id": self.agent_id,
            "own_clause_count": len(self._clauses),
            "opponent_clause_count": len(self._opponent_clauses),
            "own_clauses_str": [clause_to_str(c) for c in self._clauses],
        }

    def __len__(self) -> int:
        """Number of own clauses in the KB."""
        return len(self._clauses)

    def __repr__(self) -> str:
        return (
            f"KnowledgeBase(agent_id={self.agent_id!r}, "
            f"own={len(self._clauses)} clauses, "
            f"opponent={len(self._opponent_clauses)} clauses)"
        )
