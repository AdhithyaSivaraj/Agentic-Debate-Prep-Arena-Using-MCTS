"""
test_resolution.py — Unit tests for the propositional resolution algorithm.
Phase 1: hand-crafted contradiction examples — verifying each case before any LLM data is involved.

Test strategy:
    All inputs are hand-written so we know the ground truth exactly.
    Tests go from simplest (single-step resolution) to complex (chain inference).
    Every test checks both the boolean result AND the structural quality of the output
    (proof steps exist, conflicting clauses are named, etc.).
"""
import sys
import os

# Make sure the backend/app directory is on the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from core.resolution import (
    resolve,
    check_contradiction,
    is_tautology,
    negate,
    literal_to_str,
    clause_to_str,
    implication_to_clause,
    atom,
    neg_atom,
    Clause,
)


# ===========================================================================
# Tests for helper functions
# ===========================================================================

class TestNegate:
    def test_negate_positive_literal(self):
        """negate("P") should return ("NOT", "P")."""
        assert negate("P") == ("NOT", "P")

    def test_negate_negative_literal(self):
        """negate(("NOT", "P")) should return "P" (double-negation elimination)."""
        assert negate(("NOT", "P")) == "P"

    def test_negate_multi_word_atom(self):
        """negate("StressHigh") should return ("NOT", "StressHigh")."""
        assert negate("StressHigh") == ("NOT", "StressHigh")


class TestLiteralToStr:
    def test_positive_literal(self):
        assert literal_to_str("P") == "P"

    def test_negative_literal(self):
        assert literal_to_str(("NOT", "P")) == "¬P"


class TestClauseToStr:
    def test_empty_clause(self):
        """Empty clause should render as ⊥."""
        assert clause_to_str(frozenset()) == "⊥"

    def test_unit_clause(self):
        assert clause_to_str(frozenset({"P"})) == "P"

    def test_negative_unit_clause(self):
        assert clause_to_str(frozenset({("NOT", "P")})) == "¬P"


class TestIsTautology:
    def test_tautology_detected(self):
        """A clause containing both P and ¬P is a tautology."""
        assert is_tautology(frozenset({"P", ("NOT", "P")})) is True

    def test_non_tautology(self):
        assert is_tautology(frozenset({"P", "Q"})) is False

    def test_empty_clause_not_tautology(self):
        """The empty clause is ⊥ — not a tautology."""
        assert is_tautology(frozenset()) is False


class TestImplicationToClause:
    def test_basic_implication(self):
        """P → Q becomes ¬P ∨ Q."""
        result = implication_to_clause("P", "Q")
        assert result == frozenset({("NOT", "P"), "Q"})


# ===========================================================================
# Tests for the resolve() function
# ===========================================================================

class TestResolveFunction:
    def test_simple_complementary_literals_produces_empty_clause(self):
        """
        resolve({P}, {¬P}) must yield {frozenset()} — the empty clause ⊥.
        This is the simplest possible contradiction proof.
        """
        c1 = atom("P")           # {P}
        c2 = neg_atom("P")       # {¬P}
        result = resolve(c1, c2)
        assert frozenset() in result, (
            "resolve({P}, {¬P}) must produce the empty clause ⊥"
        )

    def test_resolve_with_extra_literals(self):
        """
        resolve({P, Q}, {¬P, R}) should yield {Q, R}.
        """
        c1 = frozenset({"P", "Q"})
        c2 = frozenset({("NOT", "P"), "R"})
        resolvents = resolve(c1, c2)
        assert frozenset({"Q", "R"}) in resolvents

    def test_no_complementary_literal_returns_empty_set(self):
        """
        resolve({P, Q}, {R, S}) — no shared complementary pair → return empty set.
        """
        c1 = frozenset({"P", "Q"})
        c2 = frozenset({"R", "S"})
        assert resolve(c1, c2) == set()

    def test_resolve_unit_implication(self):
        """
        resolve({¬P, Q}, {P}) should yield {Q}.
        Models modus ponens: (P → Q) and P → Q.
        """
        clause_p_implies_q = implication_to_clause("P", "Q")  # {¬P, Q}
        clause_p = atom("P")                                    # {P}
        resolvents = resolve(clause_p_implies_q, clause_p)
        assert frozenset({"Q"}) in resolvents

    def test_resolve_both_directions(self):
        """
        resolve(C1, C2) should give the same result as resolve(C2, C1).
        """
        c1 = frozenset({"P", "Q"})
        c2 = frozenset({("NOT", "P"), "R"})
        assert resolve(c1, c2) == resolve(c2, c1)


# ===========================================================================
# Tests for check_contradiction() — the main API
# ===========================================================================

class TestCheckContradictionDirect:
    def test_direct_contradiction_two_unit_clauses(self):
        """
        KB = [{P}, {¬P}]
        Resolution: resolve({P}, {¬P}) → ⊥ in one step.
        This is the minimal contradiction.
        """
        kb = [atom("P"), neg_atom("P")]
        result = check_contradiction(kb)
        assert result.found is True, "Direct unit contradiction must be detected"

    def test_direct_contradiction_proof_trace_nonempty(self):
        """Proof steps must be recorded when a contradiction is found."""
        kb = [atom("P"), neg_atom("P")]
        result = check_contradiction(kb)
        assert len(result.proof_steps) > 0, "Proof steps must be recorded"

    def test_direct_contradiction_conflicting_clauses_nonempty(self):
        """conflicting_clauses must identify the pair that produced ⊥."""
        kb = [atom("P"), neg_atom("P")]
        result = check_contradiction(kb)
        assert len(result.conflicting_clauses) > 0, "Conflicting clauses must be identified"

    def test_direct_contradiction_result_contains_empty_clause_step(self):
        """At least one proof step must mention ⊥."""
        kb = [atom("P"), neg_atom("P")]
        result = check_contradiction(kb)
        assert any("⊥" in step for step in result.proof_steps), (
            "Proof steps must include the ⊥ derivation step"
        )


class TestCheckContradictionChain:
    def test_chain_contradiction_three_clauses(self):
        """
        KB = [P → Q,  Q → R,  ¬R,  P]
        Derivation:
            resolve({¬P, Q}, {P})   → {Q}
            resolve({¬Q, R}, {Q})   → {R}
            resolve({R}, {¬R})      → ⊥
        """
        kb = [
            implication_to_clause("P", "Q"),   # P → Q  (¬P ∨ Q)
            implication_to_clause("Q", "R"),   # Q → R  (¬Q ∨ R)
            neg_atom("R"),                     # ¬R
            atom("P"),                         # P
        ]
        result = check_contradiction(kb)
        assert result.found is True, (
            "Chain contradiction (P→Q, Q→R, ¬R, P) must be detected"
        )

    def test_chain_contradiction_exam_stress_health_scenario(self):
        """
        Real-world-flavoured example matching the project's debate domain:
            ExamsAbolished → StressLow    (abolishing exams reduces stress)
            ¬StressLow                   (but stress is NOT low — a claim from opponent)
            ExamsAbolished               (we assert exams are abolished)

        Derivation:
            resolve({¬ExamsAbolished, StressLow}, {ExamsAbolished}) → {StressLow}
            resolve({StressLow}, {¬StressLow})                      → ⊥
        """
        kb = [
            implication_to_clause("ExamsAbolished", "StressLow"),
            neg_atom("StressLow"),
            atom("ExamsAbolished"),
        ]
        result = check_contradiction(kb)
        assert result.found is True, (
            "Exam-stress chain contradiction must be detected"
        )

    def test_deeper_chain_four_hops(self):
        """
        KB = [A → B,  B → C,  C → D,  ¬D,  A]
        Tests that the algorithm handles longer derivation chains.
        """
        kb = [
            implication_to_clause("A", "B"),
            implication_to_clause("B", "C"),
            implication_to_clause("C", "D"),
            neg_atom("D"),
            atom("A"),
        ]
        result = check_contradiction(kb)
        assert result.found is True, "Four-hop chain contradiction must be detected"


class TestCheckContradictionConsistentKB:
    def test_single_positive_literal_is_consistent(self):
        """KB = [{P}] — no contradiction possible."""
        kb = [atom("P")]
        result = check_contradiction(kb)
        assert result.found is False

    def test_two_unrelated_literals_are_consistent(self):
        """KB = [{P}, {Q}] — no shared atoms, no contradiction."""
        kb = [atom("P"), atom("Q")]
        result = check_contradiction(kb)
        assert result.found is False

    def test_implication_and_antecedent_consistent(self):
        """
        KB = [P → Q,  P]
        Derives Q, but that's not a contradiction — KB is consistent.
        """
        kb = [implication_to_clause("P", "Q"), atom("P")]
        result = check_contradiction(kb)
        assert result.found is False

    def test_implication_chain_without_negation_is_consistent(self):
        """
        KB = [P → Q,  Q → R,  P]
        Derives Q then R — all internally consistent, no negation.
        """
        kb = [
            implication_to_clause("P", "Q"),
            implication_to_clause("Q", "R"),
            atom("P"),
        ]
        result = check_contradiction(kb)
        assert result.found is False

    def test_consistent_kb_has_empty_conflicting_clauses(self):
        """When found=False, conflicting_clauses must be empty."""
        kb = [atom("P"), atom("Q")]
        result = check_contradiction(kb)
        assert result.conflicting_clauses == []

    def test_empty_kb_is_consistent(self):
        """An empty KB has no clauses to contradict — trivially consistent."""
        result = check_contradiction([])
        assert result.found is False


class TestContradictionResult:
    def test_result_is_named_tuple_with_correct_fields(self):
        """ContradictionResult must expose found, conflicting_clauses, proof_steps."""
        kb = [atom("P"), neg_atom("P")]
        result = check_contradiction(kb)
        assert hasattr(result, "found")
        assert hasattr(result, "conflicting_clauses")
        assert hasattr(result, "proof_steps")

    def test_conflicting_clauses_are_strings_not_frozensets(self):
        """
        The UI needs human-readable strings, not raw frozensets.
        Each entry in conflicting_clauses must be a tuple of two strings.
        """
        kb = [atom("P"), neg_atom("P")]
        result = check_contradiction(kb)
        assert result.found is True
        for pair in result.conflicting_clauses:
            assert isinstance(pair, tuple), "Each conflict entry must be a tuple"
            assert len(pair) == 2, "Each conflict entry must be a pair"
            assert isinstance(pair[0], str), "Clause display strings must be str"
            assert isinstance(pair[1], str), "Clause display strings must be str"

    def test_proof_steps_are_strings(self):
        """Each proof step must be a human-readable string."""
        kb = [atom("P"), neg_atom("P")]
        result = check_contradiction(kb)
        for step in result.proof_steps:
            assert isinstance(step, str)


class TestEdgeCases:
    def test_single_clause_cannot_be_contradictory(self):
        """A single clause is trivially satisfiable — no self-contradiction."""
        kb = [frozenset({"P", "Q", ("NOT", "R")})]
        result = check_contradiction(kb)
        assert result.found is False

    def test_contradiction_found_is_deterministic(self):
        """
        Running check_contradiction twice on the same KB must give the same result.
        (The algorithm must be deterministic — no randomness.)
        """
        kb = [atom("P"), neg_atom("P")]
        r1 = check_contradiction(kb)
        r2 = check_contradiction(kb)
        assert r1.found == r2.found

    def test_ordering_does_not_affect_result(self):
        """
        The contradiction result must not depend on clause order in the list.
        KB = [¬P, P] should give the same result as KB = [P, ¬P].
        """
        kb_a = [atom("P"), neg_atom("P")]
        kb_b = [neg_atom("P"), atom("P")]
        r_a = check_contradiction(kb_a)
        r_b = check_contradiction(kb_b)
        assert r_a.found == r_b.found
