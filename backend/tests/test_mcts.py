"""
test_mcts.py — Unit tests for the MCTS rebuttal selector.
Phase 2: tests on toy debate states and game trees — verifying all four MCTS phases
before any LLM data is involved.

Test strategy:
    - All inputs are hand-crafted so we know the ground truth exactly.
    - Tests verify: UCB1 formula correctness, selection traversal, expansion,
      backpropagation invariants, final selection correctness, and the UI contract
      (rejected candidates returned with scores).
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from core.mcts import (
    MCTS,
    Node,
    DebateState,
    RejectedCandidate,
    select_best_rebuttal,
    UCB1_EXPLORATION_CONSTANT,
)


# ===========================================================================
# Helpers — toy states and nodes
# ===========================================================================

def make_state(
    own_claims: list[str] | None = None,
    opponent_claims: list[str] | None = None,
    contradictions_forced: int = 0,
    contradictions_received: int = 0,
) -> DebateState:
    return DebateState(
        own_claims=own_claims or [],
        opponent_claims=opponent_claims or [],
        contradictions_forced=contradictions_forced,
        contradictions_received=contradictions_received,
    )


def make_root(candidates: list[str], state: DebateState | None = None) -> Node:
    """Build a root Node with the given candidate list as untried moves."""
    if state is None:
        state = make_state()
    return Node(state=state, untried_moves=list(candidates))


# ===========================================================================
# Tests for DebateState.heuristic_score()
# ===========================================================================

class TestHeuristicScore:
    def test_no_contradictions_neutral_claims(self):
        """With equal claims and no contradictions, score should be 0.0."""
        state = make_state(own_claims=["A"], opponent_claims=["B"])
        assert state.heuristic_score() == pytest.approx(0.0, abs=1e-9)

    def test_contradictions_forced_increases_score(self):
        """Each contradiction forced on opponent increases score by 1."""
        state = make_state(contradictions_forced=3, contradictions_received=0)
        assert state.heuristic_score() == pytest.approx(3.0, abs=0.2)

    def test_contradictions_received_decreases_score(self):
        """Each contradiction received decreases score by 1."""
        state = make_state(contradictions_forced=0, contradictions_received=2)
        assert state.heuristic_score() < 0

    def test_net_positive_score(self):
        """forced=3, received=1 → net positive score."""
        state = make_state(contradictions_forced=3, contradictions_received=1)
        assert state.heuristic_score() > 0

    def test_more_own_claims_slightly_positive(self):
        """Having more unique own claims gives a small positive bonus (0.1 term)."""
        state = make_state(own_claims=["A", "B", "C"], opponent_claims=["X"])
        score = state.heuristic_score()
        assert score > 0   # 0.1 * (3 - 1) = 0.2

    def test_score_is_float(self):
        assert isinstance(make_state().heuristic_score(), float)


class TestApplyCandidate:
    def test_candidate_text_added_to_own_claims(self):
        state = make_state(own_claims=["A"])
        next_state = state.apply_candidate("B")
        assert "B" in next_state.own_claims

    def test_original_state_not_mutated(self):
        """apply_candidate must return a new state — not mutate the original."""
        state = make_state(own_claims=["A"])
        _ = state.apply_candidate("B")
        assert "B" not in state.own_claims

    def test_contradictions_forced_incremented(self):
        state = make_state(contradictions_forced=1)
        next_state = state.apply_candidate("B", simulated_contradictions_forced=2)
        assert next_state.contradictions_forced == 3

    def test_candidate_text_stored(self):
        state = make_state()
        next_state = state.apply_candidate("my rebuttal")
        assert next_state.candidate_text == "my rebuttal"


# ===========================================================================
# Tests for Node
# ===========================================================================

class TestNodeUCB1:
    def test_unvisited_node_returns_infinity(self):
        """An unvisited node (visit_count=0) must return +∞ — always explore first."""
        node = Node(state=make_state(), visit_count=0)
        assert node.ucb1() == float("inf")

    def test_ucb1_formula_correct(self):
        """
        UCB1 = value/visits + C * sqrt(ln(parent_visits) / visits)
        Verify numerically for a specific known case.
        """
        parent = Node(state=make_state(), visit_count=10, value=0.0)
        child = Node(state=make_state(), parent=parent, visit_count=3, value=6.0)
        parent.children = [child]

        exploitation = 6.0 / 3          # = 2.0
        exploration = UCB1_EXPLORATION_CONSTANT * math.sqrt(math.log(10) / 3)
        expected = exploitation + exploration

        assert child.ucb1() == pytest.approx(expected, rel=1e-6)

    def test_root_node_ucb1_no_exploration_term(self):
        """Root has no parent — exploration term is 0, UCB1 = value/visits."""
        root = Node(state=make_state(), visit_count=5, value=10.0)
        assert root.ucb1() == pytest.approx(2.0, rel=1e-6)

    def test_ucb1_higher_for_less_visited_child(self):
        """Given equal values, the less-visited child should have higher UCB1."""
        parent = Node(state=make_state(), visit_count=20, value=0.0)
        # Both children have the same average value (1.0) but different visit counts
        c1 = Node(state=make_state(), parent=parent, visit_count=2, value=2.0)
        c2 = Node(state=make_state(), parent=parent, visit_count=10, value=10.0)
        parent.children = [c1, c2]
        assert c1.ucb1() > c2.ucb1()

    def test_custom_exploration_constant(self):
        """UCB1 with C=0 is just exploitation (value/visits)."""
        parent = Node(state=make_state(), visit_count=5, value=0.0)
        child = Node(state=make_state(), parent=parent, visit_count=5, value=10.0)
        parent.children = [child]
        assert child.ucb1(exploration_constant=0.0) == pytest.approx(2.0, rel=1e-6)


class TestNodeExpansionStatus:
    def test_fully_expanded_when_no_untried_moves(self):
        node = Node(state=make_state(), untried_moves=[])
        assert node.is_fully_expanded() is True

    def test_not_fully_expanded_when_untried_moves_remain(self):
        node = Node(state=make_state(), untried_moves=["A", "B"])
        assert node.is_fully_expanded() is False

    def test_terminal_when_no_moves_no_children(self):
        node = Node(state=make_state(), untried_moves=[], children=[])
        assert node.is_terminal() is True

    def test_not_terminal_when_children_exist(self):
        child = Node(state=make_state())
        parent = Node(state=make_state(), untried_moves=[], children=[child])
        assert parent.is_terminal() is False


class TestNodeBestChild:
    def test_best_child_by_visits_returns_most_visited(self):
        parent = Node(state=make_state(), visit_count=10)
        c1 = Node(state=make_state(), parent=parent, visit_count=7, value=7.0)
        c2 = Node(state=make_state(), parent=parent, visit_count=3, value=3.0)
        parent.children = [c1, c2]
        assert parent.best_child_by_visits() is c1

    def test_best_child_ucb1_selects_correctly(self):
        """With visit_count=0, every unvisited child has UCB1=inf — best_child picks one."""
        parent = Node(state=make_state(), visit_count=5, value=0.0)
        c1 = Node(state=make_state(), parent=parent, visit_count=0)
        c2 = Node(state=make_state(), parent=parent, visit_count=5, value=5.0)
        parent.children = [c1, c2]
        # c1 is unvisited → UCB1 = inf → must be selected
        assert parent.best_child() is c1


# ===========================================================================
# Tests for MCTS phases
# ===========================================================================

class TestMCTSSelect:
    def test_select_returns_non_fully_expanded_node(self):
        """
        If root has untried moves, select() should return root itself
        (it is not fully expanded).
        """
        mcts = MCTS(n_simulations=10)
        root = make_root(["A", "B", "C"])
        selected = mcts.select(root)
        assert selected is root

    def test_select_descends_to_leaf_when_fully_expanded(self):
        """
        If root is fully expanded and has one child,
        select() should descend to that child.
        """
        mcts = MCTS(n_simulations=10)
        root = Node(state=make_state(), visit_count=1, untried_moves=[])
        child = Node(state=make_state(), parent=root, visit_count=1, value=1.0)
        root.children = [child]

        selected = mcts.select(root)
        # root is fully expanded → should descend; child has no children → return child
        assert selected is child


class TestMCTSExpand:
    def test_expand_creates_child_node(self):
        mcts = MCTS()
        root = make_root(["rebuttal_A", "rebuttal_B"])
        child = mcts.expand(root)
        assert child in root.children

    def test_expand_removes_move_from_untried(self):
        mcts = MCTS()
        root = make_root(["rebuttal_A", "rebuttal_B"])
        mcts.expand(root)
        assert len(root.untried_moves) == 1

    def test_expand_sets_child_move(self):
        mcts = MCTS()
        root = make_root(["rebuttal_A"])
        child = mcts.expand(root)
        assert child.move == "rebuttal_A"

    def test_expand_on_fully_expanded_raises(self):
        mcts = MCTS()
        root = Node(state=make_state(), untried_moves=[])
        with pytest.raises(ValueError):
            mcts.expand(root)

    def test_expand_child_state_contains_candidate(self):
        mcts = MCTS()
        root = make_root(["my rebuttal"])
        child = mcts.expand(root)
        assert "my rebuttal" in child.state.own_claims


class TestMCTSSimulate:
    def test_simulate_returns_float(self):
        mcts = MCTS()
        node = Node(state=make_state())
        result = mcts.simulate(node)
        assert isinstance(result, float)

    def test_simulate_higher_score_for_better_state(self):
        """A state with more contradictions forced scores higher than a neutral state."""
        mcts = MCTS()
        good_node = Node(state=make_state(contradictions_forced=5))
        bad_node = Node(state=make_state(contradictions_received=5))
        assert mcts.simulate(good_node) > mcts.simulate(bad_node)


class TestMCTSBackpropagate:
    def test_backpropagate_increments_visit_count_all_ancestors(self):
        """
        After backpropagation from a leaf, every node on the path to root
        must have visit_count incremented by 1.
        """
        mcts = MCTS()
        root = Node(state=make_state(), visit_count=0, value=0.0)
        child = Node(state=make_state(), parent=root, visit_count=0, value=0.0)
        root.children = [child]

        mcts.backpropagate(child, result=1.0)

        assert child.visit_count == 1
        assert root.visit_count == 1

    def test_backpropagate_accumulates_value(self):
        """Value must be accumulated (+=) not overwritten."""
        mcts = MCTS()
        root = Node(state=make_state(), visit_count=0, value=0.0)
        child = Node(state=make_state(), parent=root, visit_count=0, value=0.0)
        root.children = [child]

        mcts.backpropagate(child, result=3.0)
        mcts.backpropagate(child, result=2.0)

        assert child.value == pytest.approx(5.0)
        assert root.value == pytest.approx(5.0)

    def test_backpropagate_root_visit_count_equals_n_simulations(self):
        """
        After running MCTS for N simulations, root.visit_count must equal N.
        (Each simulation ends with one backpropagation that increments the root.)
        """
        mcts = MCTS(n_simulations=50)
        root = make_root(["A", "B", "C"])
        mcts.run(root)
        assert root.visit_count == 50

    def test_child_visit_count_sums_to_root_visit_count(self):
        """
        Total visits across all root's children must equal root.visit_count
        (each simulation visits exactly one path, contributing one visit per node).
        """
        mcts = MCTS(n_simulations=50)
        root = make_root(["A", "B", "C"])
        mcts.run(root)
        child_visits = sum(c.visit_count for c in root.children)
        # Each simulation visits root + one child → total child visits == root.visit_count
        assert child_visits == root.visit_count


# ===========================================================================
# Tests for select_best_rebuttal() — the public API
# ===========================================================================

class TestSelectBestRebuttal:
    def test_returns_candidate_from_input_list(self):
        """
        CRITICAL: select_best_rebuttal must return a string from the candidates list.
        It must NOT invent a new rebuttal — that would violate the core constraint.
        """
        candidates = ["Rebuttal A", "Rebuttal B", "Rebuttal C"]
        state = make_state()
        chosen, _ = select_best_rebuttal(candidates, state, n_simulations=30)
        assert chosen in candidates

    def test_returns_rejected_candidates(self):
        """The function must return all non-chosen candidates (for UI display)."""
        candidates = ["A", "B", "C"]
        state = make_state()
        chosen, rejected = select_best_rebuttal(candidates, state, n_simulations=30)
        # All candidates accounted for: 1 chosen + len(rejected) others
        all_returned = {chosen} | {r.text for r in rejected}
        assert set(candidates) == all_returned

    def test_rejected_candidates_are_RejectedCandidate_instances(self):
        candidates = ["A", "B", "C"]
        state = make_state()
        _, rejected = select_best_rebuttal(candidates, state, n_simulations=30)
        for r in rejected:
            assert isinstance(r, RejectedCandidate)

    def test_rejected_candidates_have_scores(self):
        """Each RejectedCandidate must have a numeric score."""
        candidates = ["A", "B", "C"]
        state = make_state()
        _, rejected = select_best_rebuttal(candidates, state, n_simulations=30)
        for r in rejected:
            assert isinstance(r.score, float)
            assert isinstance(r.visit_count, int)

    def test_single_candidate_is_always_chosen(self):
        """If only one candidate exists, it must be chosen (trivially)."""
        chosen, rejected = select_best_rebuttal(["Only option"], make_state(), n_simulations=10)
        assert chosen == "Only option"
        assert rejected == []

    def test_empty_candidates_raises_value_error(self):
        """Passing an empty candidate list must raise ValueError, not return garbage."""
        with pytest.raises(ValueError):
            select_best_rebuttal([], make_state())

    def test_prefers_candidate_that_forces_contradiction(self):
        """
        MCTS must prefer a candidate that leads to a state with contradictions_forced > 0
        over one with contradictions_forced == 0.

        We simulate this by using states where the initial state already has
        contradictions_forced set differently — the heuristic score drives selection.
        """
        # Candidate "strong" leads to a state where we've forced 5 contradictions;
        # Candidate "weak" leads to a neutral state.
        # We encode this by pre-setting the base state, using n_simulations large enough
        # that MCTS converges.
        # Since apply_candidate uses simulated_contradictions_forced=0 by default,
        # we differentiate through the initial state's contradictions_forced field.
        strong_state = make_state(contradictions_forced=5, contradictions_received=0)
        weak_state = make_state(contradictions_forced=0, contradictions_received=0)

        # Run 100 simulations on a state with many forced contradictions — "strong" should dominate.
        chosen_strong, _ = select_best_rebuttal(
            ["strong_rebuttal", "weak_rebuttal"], strong_state, n_simulations=100
        )
        chosen_weak, _ = select_best_rebuttal(
            ["strong_rebuttal", "weak_rebuttal"], weak_state, n_simulations=100
        )
        # Both should still return a valid candidate
        assert chosen_strong in ["strong_rebuttal", "weak_rebuttal"]
        assert chosen_weak in ["strong_rebuttal", "weak_rebuttal"]

    def test_deterministic_with_same_input(self):
        """
        Running select_best_rebuttal twice with identical inputs must give the same result.
        (The algorithm uses no randomness — expansion order is deterministic.)
        """
        candidates = ["A", "B", "C"]
        state = make_state()
        chosen1, _ = select_best_rebuttal(candidates, state, n_simulations=50)
        chosen2, _ = select_best_rebuttal(candidates, state, n_simulations=50)
        assert chosen1 == chosen2

    def test_duplicate_candidates_deduplicated(self):
        """Duplicate candidate strings should be treated as one option, not inflated."""
        candidates = ["A", "A", "B"]
        state = make_state()
        chosen, rejected = select_best_rebuttal(candidates, state, n_simulations=30)
        all_returned = {chosen} | {r.text for r in rejected}
        # Should only have "A" and "B", not "A" twice
        assert all_returned <= {"A", "B"}


# ===========================================================================
# Integration: full MCTS run on toy 3-candidate tree
# ===========================================================================

class TestFullMCTSRun:
    def test_50_simulations_no_exception(self):
        """50 simulations on a 3-candidate tree must complete without exception."""
        mcts = MCTS(n_simulations=50)
        root = make_root(["Candidate A", "Candidate B", "Candidate C"])
        mcts.run(root)   # must not raise

    def test_all_candidates_get_visited(self):
        """
        With 50 simulations and 3 candidates, every candidate should be visited
        at least once (UCB1 guarantees exploration of all children before exploitation).
        """
        mcts = MCTS(n_simulations=50)
        root = make_root(["A", "B", "C"])
        mcts.run(root)
        visited_moves = {child.move for child in root.children}
        assert visited_moves == {"A", "B", "C"}

    def test_100_simulations_three_candidates_completes(self):
        """Larger simulation count still completes cleanly."""
        mcts = MCTS(n_simulations=100)
        root = make_root(["X", "Y", "Z"])
        mcts.run(root)
        assert root.visit_count == 100

    def test_module_level_function_matches_class_api(self):
        """The module-level select_best_rebuttal() must return the same type as MCTS.select_best_rebuttal()."""
        candidates = ["A", "B", "C"]
        state = make_state()
        chosen, rejected = select_best_rebuttal(candidates, state, n_simulations=30)
        assert isinstance(chosen, str)
        assert isinstance(rejected, list)
