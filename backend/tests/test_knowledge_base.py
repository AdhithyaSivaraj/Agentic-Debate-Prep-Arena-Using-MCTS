"""
test_knowledge_base.py — Unit tests for the KnowledgeBase TELL/ASK interface.
Phase 3: verifying the KB-agent pattern using the resolution engine from Phase 1.

All contradiction detection is done by resolution.py — these tests confirm
that KnowledgeBase correctly wraps and delegates to it.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from core.knowledge_base import KnowledgeBase
from core.resolution import atom, neg_atom, implication_to_clause


# ===========================================================================
# Tests for TELL
# ===========================================================================

class TestTell:
    def test_tell_adds_clause_to_kb(self):
        kb = KnowledgeBase("agent_a")
        clause = atom("P")
        kb.tell(clause)
        assert clause in kb.get_all_clauses()

    def test_tell_duplicate_is_ignored(self):
        """Asserting the same clause twice must not create a duplicate entry."""
        kb = KnowledgeBase("agent_a")
        clause = atom("P")
        kb.tell(clause)
        kb.tell(clause)
        assert len(kb.get_all_clauses()) == 1

    def test_tell_increments_length(self):
        kb = KnowledgeBase("agent_a")
        assert len(kb) == 0
        kb.tell(atom("P"))
        assert len(kb) == 1
        kb.tell(atom("Q"))
        assert len(kb) == 2

    def test_tell_stores_human_readable_history(self):
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"), human_readable="Exams cause stress")
        assert "Exams cause stress" in kb.get_history()

    def test_tell_opponent_adds_to_opponent_clauses(self):
        kb = KnowledgeBase("agent_a")
        clause = atom("Q")
        kb.tell_opponent(clause)
        assert clause in kb.get_opponent_clauses()
        assert clause not in kb.get_all_clauses()

    def test_tell_opponent_duplicate_ignored(self):
        kb = KnowledgeBase("agent_a")
        clause = atom("Q")
        kb.tell_opponent(clause)
        kb.tell_opponent(clause)
        assert len(kb.get_opponent_clauses()) == 1

    def test_tell_multiple_clauses_preserves_order(self):
        """Clauses should be stored in insertion order (for proof trace readability)."""
        kb = KnowledgeBase("agent_a")
        clauses = [atom("A"), atom("B"), atom("C")]
        for c in clauses:
            kb.tell(c)
        stored = kb.get_all_clauses()
        assert stored == clauses


# ===========================================================================
# Tests for ASK — own KB contradiction
# ===========================================================================

class TestAskContradiction:
    def test_empty_kb_is_not_contradictory(self):
        kb = KnowledgeBase("agent_a")
        result = kb.ask_contradiction()
        assert result.found is False

    def test_single_clause_kb_is_not_contradictory(self):
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"))
        result = kb.ask_contradiction()
        assert result.found is False

    def test_direct_contradiction_detected(self):
        """KB = [{P}, {¬P}] → found=True."""
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"))
        kb.tell(neg_atom("P"))
        result = kb.ask_contradiction()
        assert result.found is True

    def test_chain_contradiction_detected(self):
        """KB = [P→Q, ¬Q, P] → found=True via resolution chain."""
        kb = KnowledgeBase("agent_a")
        kb.tell(implication_to_clause("P", "Q"))
        kb.tell(neg_atom("Q"))
        kb.tell(atom("P"))
        result = kb.ask_contradiction()
        assert result.found is True

    def test_consistent_kb_not_contradictory(self):
        """KB = [P→Q, P] → consistent, found=False."""
        kb = KnowledgeBase("agent_a")
        kb.tell(implication_to_clause("P", "Q"))
        kb.tell(atom("P"))
        result = kb.ask_contradiction()
        assert result.found is False

    def test_contradiction_result_has_proof_steps(self):
        """When found=True, proof_steps must be non-empty."""
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"))
        kb.tell(neg_atom("P"))
        result = kb.ask_contradiction()
        assert result.found is True
        assert len(result.proof_steps) > 0

    def test_contradiction_result_has_conflicting_clauses(self):
        """When found=True, conflicting_clauses must name the offending pair."""
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"))
        kb.tell(neg_atom("P"))
        result = kb.ask_contradiction()
        assert len(result.conflicting_clauses) > 0


# ===========================================================================
# Tests for ASK — opponent KB contradiction
# ===========================================================================

class TestAskOpponentContradiction:
    def test_empty_opponent_kb_is_consistent(self):
        kb = KnowledgeBase("agent_a")
        result = kb.ask_contradiction_of_opponent()
        assert result.found is False

    def test_opponent_self_contradiction_detected(self):
        """Opponent asserts P and ¬P — should be caught."""
        kb = KnowledgeBase("agent_a")
        kb.tell_opponent(atom("P"))
        kb.tell_opponent(neg_atom("P"))
        result = kb.ask_contradiction_of_opponent()
        assert result.found is True

    def test_own_contradiction_doesnt_affect_opponent_check(self):
        """
        Even if own KB is contradictory, ask_contradiction_of_opponent should
        only look at opponent clauses.
        """
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"))
        kb.tell(neg_atom("P"))           # own contradiction
        kb.tell_opponent(atom("Q"))      # opponent is consistent
        result = kb.ask_contradiction_of_opponent()
        assert result.found is False


# ===========================================================================
# Tests for ASK — combined (cross-agent) contradiction
# ===========================================================================

class TestAskCombinedContradiction:
    def test_combined_contradiction_across_agents(self):
        """
        Own KB says P; opponent KB says ¬P.
        Combined check must find the contradiction.
        """
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"))
        kb.tell_opponent(neg_atom("P"))
        result = kb.ask_combined_contradiction()
        assert result.found is True

    def test_combined_consistent_when_no_cross_conflict(self):
        """
        Own KB says P; opponent KB says Q. No shared atoms → consistent.
        """
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"))
        kb.tell_opponent(atom("Q"))
        result = kb.ask_combined_contradiction()
        assert result.found is False


# ===========================================================================
# Tests for utility methods
# ===========================================================================

class TestUtilities:
    def test_get_all_clauses_returns_copy(self):
        """Mutating the returned list must not affect the internal KB."""
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"))
        clauses = kb.get_all_clauses()
        clauses.clear()
        assert len(kb) == 1

    def test_summary_contains_expected_keys(self):
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"))
        s = kb.summary()
        assert "agent_id" in s
        assert "own_clause_count" in s
        assert "own_clauses_str" in s

    def test_summary_own_clause_count_matches_len(self):
        kb = KnowledgeBase("agent_a")
        kb.tell(atom("P"))
        kb.tell(atom("Q"))
        assert kb.summary()["own_clause_count"] == 2

    def test_repr_contains_agent_id(self):
        kb = KnowledgeBase("agent_b")
        assert "agent_b" in repr(kb)

    def test_two_kbs_are_independent(self):
        """Each agent's KB must be completely independent."""
        kb_a = KnowledgeBase("agent_a")
        kb_b = KnowledgeBase("agent_b")
        kb_a.tell(atom("P"))
        assert len(kb_b) == 0
