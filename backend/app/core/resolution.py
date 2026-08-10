"""
resolution.py — Propositional Resolution Algorithm (Unit IV: Propositional Theorem Proving)

This is the algorithmic core for contradiction detection.

KEY CONSTRAINT (must never be violated):
    The LLM must NEVER decide whether something is a contradiction.
    Only the algorithm in this file makes that determination — it is provable,
    deterministic, and fully auditable (the "explainable AI" claim from the master prompt).

=== REPRESENTATION ===

A *literal* is either a positive atom or a negated atom:
    - Positive:  the string itself,  e.g.  "ExamsAbolished"
    - Negative:  a tuple ("NOT", atom), e.g. ("NOT", "ExamsAbolished")

A *clause* is a frozenset of literals — the disjunction of those literals.
    e.g.  frozenset({"ExamsAbolished", ("NOT", "StressHigh")})
    means  ExamsAbolished ∨ ¬StressHigh

An implication  P → Q  is stored as  ¬P ∨ Q:
    frozenset({("NOT", "P"), "Q"})

=== ALGORITHM ===

Resolution refutation:
    Given a KB of clauses, add the negated goal and attempt to derive the empty clause ⊥.
    If ⊥ is derived, the KB is unsatisfiable (contradictory).

    check_contradiction(kb) uses Robinson's resolution algorithm:
        1. Start with the set of all clauses in kb.
        2. For every pair of clauses (C1, C2), compute all resolvents.
        3. If any resolvent is ⊥ (empty clause), return ContradictionResult(found=True, ...).
        4. If a new resolvent is not already in the clause set, add it and repeat.
        5. If no new clauses can be added, return ContradictionResult(found=False, ...).

    This is complete for propositional logic (Robinson's completeness theorem).
"""
from __future__ import annotations
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

# A literal: either a plain string (positive) or a ("NOT", str) tuple (negated)
Literal = str | tuple[str, str]

# A clause: a frozenset of literals (disjunction)
Clause = frozenset


class ContradictionResult(NamedTuple):
    """
    Result returned by check_contradiction().

    found:               True if the resolution algorithm derived ⊥ (empty clause).
    conflicting_clauses: The specific clause pair(s) that produced ⊥.
                         Each entry is a pair (clause1_str, clause2_str) for UI display.
    proof_steps:         Human-readable trace of every resolution step taken.
                         Formatted as:  "RESOLVE {C1} + {C2}  →  {resolvent}"
    """
    found: bool
    conflicting_clauses: list[tuple[str, str]]
    proof_steps: list[str]


# ---------------------------------------------------------------------------
# Literal helpers
# ---------------------------------------------------------------------------

def negate(literal: Literal) -> Literal:
    """
    Return the negation of a literal.
        negate("P")           →  ("NOT", "P")
        negate(("NOT", "P"))  →  "P"
    """
    if isinstance(literal, tuple) and literal[0] == "NOT":
        return literal[1]          # double-negation elimination
    return ("NOT", literal)        # wrap positive literal in NOT


def literal_to_str(literal: Literal) -> str:
    """Human-readable string for a literal — used in proof traces."""
    if isinstance(literal, tuple) and literal[0] == "NOT":
        return f"¬{literal[1]}"
    return str(literal)


def clause_to_str(clause: Clause) -> str:
    """Human-readable string for a clause — used in proof traces and UI."""
    if not clause:
        return "⊥"   # empty clause = contradiction
    return " ∨ ".join(sorted(literal_to_str(lit) for lit in clause))


# ---------------------------------------------------------------------------
# Resolution rule
# ---------------------------------------------------------------------------

def resolve(c1: Clause, c2: Clause) -> set[Clause]:
    """
    Apply the propositional resolution rule between two clauses.

    For every literal L in c1 such that ¬L ∈ c2:
        Produce the resolvent:  (c1 − {L}) ∪ (c2 − {¬L})

    Returns the set of all resolvents (typically 0 or 1, but multiple are possible
    if there are multiple complementary pairs — we include all of them).

    Examples:
        resolve({P}, {¬P})         →  {frozenset()}       (empty clause ⊥)
        resolve({P, Q}, {¬P, R})   →  {frozenset({Q, R})}
        resolve({P, Q}, {R, S})    →  set()               (no complementary pair)
        resolve({P, ¬P}, {¬P})     →  {frozenset({¬P}), frozenset({P})}
                                       (tautological resolvents are included;
                                        they're filtered out in the main loop)
    """
    resolvents: set[Clause] = set()

    for literal in c1:
        complement = negate(literal)
        if complement in c2:
            # Form the resolvent by removing the complementary pair
            resolvent = frozenset(
                (c1 - frozenset({literal})) | (c2 - frozenset({complement}))
            )
            resolvents.add(resolvent)

    return resolvents


# ---------------------------------------------------------------------------
# Tautology check
# ---------------------------------------------------------------------------

def is_tautology(clause: Clause) -> bool:
    """
    A clause is a tautology if it contains both L and ¬L for any literal L.
    Tautologies are always true and can be pruned — they never help derive ⊥.
    """
    for literal in clause:
        if negate(literal) in clause:
            return True
    return False


# ---------------------------------------------------------------------------
# Main contradiction check
# ---------------------------------------------------------------------------

def check_contradiction(kb: list[Clause]) -> ContradictionResult:
    """
    Run propositional resolution refutation on the given knowledge base.

    Uses Robinson's saturation algorithm:
        - Repeatedly resolve all pairs of clauses.
        - If ⊥ (empty clause) is derived → KB is unsatisfiable → contradiction found.
        - If no new clause can be added → KB is satisfiable → no contradiction.

    Returns a ContradictionResult with:
        - found=True/False
        - conflicting_clauses: the pair that produced ⊥ (for the UI proof-trace panel)
        - proof_steps: every resolution step taken (full derivation trace)

    Note: this operates on the KB as-is. The caller (KnowledgeBase.ask_contradiction)
    is responsible for deciding whether to negate a goal before calling this function.
    For contradiction detection in a debate KB, no negated goal is needed — we just
    check whether the KB's own clauses are mutually consistent.
    """
    # Working set of clauses — use a list to preserve insertion order for proof steps,
    # and a set for fast membership testing.
    clauses: list[Clause] = list(kb)
    clause_set: set[Clause] = set(kb)

    proof_steps: list[str] = []
    conflicting_pair: tuple[str, str] | None = None

    # Iterative resolution — keep going until no new clause is added or ⊥ is found
    changed = True
    while changed:
        changed = False
        # Generate all pairs — iterate over a snapshot so new additions
        # are caught in the next outer iteration
        current_clauses = list(clauses)
        n = len(current_clauses)

        for i in range(n):
            for j in range(i + 1, n):
                c1 = current_clauses[i]
                c2 = current_clauses[j]
                resolvents = resolve(c1, c2)

                for resolvent in resolvents:
                    step_str = (
                        f"RESOLVE  {{{clause_to_str(c1)}}}  +  "
                        f"{{{clause_to_str(c2)}}}  →  {{{clause_to_str(resolvent)}}}"
                    )

                    # Check for ⊥ (empty clause)
                    if len(resolvent) == 0:
                        proof_steps.append(step_str)
                        conflicting_pair = (
                            clause_to_str(c1),
                            clause_to_str(c2),
                        )
                        return ContradictionResult(
                            found=True,
                            conflicting_clauses=[conflicting_pair],
                            proof_steps=proof_steps,
                        )

                    # Skip tautologies — they add no information
                    if is_tautology(resolvent):
                        continue

                    # Add only genuinely new clauses
                    if resolvent not in clause_set:
                        proof_steps.append(step_str)
                        clause_set.add(resolvent)
                        clauses.append(resolvent)
                        changed = True

    # Exhausted all resolvents — no ⊥ derived → KB is consistent
    return ContradictionResult(
        found=False,
        conflicting_clauses=[],
        proof_steps=proof_steps,
    )


# ---------------------------------------------------------------------------
# Convenience: parse implication strings into clauses
# ---------------------------------------------------------------------------

def implication_to_clause(antecedent: str, consequent: str) -> Clause:
    """
    Convert  antecedent → consequent  into clause form  ¬antecedent ∨ consequent.

    Usage:
        implication_to_clause("Exams", "StressHigh")
        →  frozenset({("NOT", "Exams"), "StressHigh"})

    This is a convenience helper for tests and for the fact-normalization pipeline.
    """
    return frozenset({("NOT", antecedent), consequent})


def atom(name: str) -> Clause:
    """
    Convenience: a unit clause containing a single positive literal.
        atom("P")  →  frozenset({"P"})
    """
    return frozenset({name})


def neg_atom(name: str) -> Clause:
    """
    Convenience: a unit clause containing a single negative literal.
        neg_atom("P")  →  frozenset({("NOT", "P")})
    """
    return frozenset({("NOT", name)})
