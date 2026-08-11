"""
mcts.py — Monte Carlo Tree Search for Rebuttal Selection (Unit III: Adversarial Search / Game Theory)

This is the move-selection core of the debate engine.

KEY CONSTRAINT (must never be violated):
    The LLM must NEVER decide what the best rebuttal is.
    Only this MCTS implementation makes that determination — provably, deterministically,
    and in a way that can be visualised step-by-step for the UI's "show your work" panel.

=== FRAMING: DEBATE AS AN ADVERSARIAL GAME ===

Each rebuttal-selection call is framed as a two-player, zero-sum-ish game:
    - "Our" agent wants to maximise contradictions forced on the opponent.
    - The opponent wants to do the same.
    - A "game state" is the debate's snapshot at a given turn, carrying enough
      information to score a simulated follow-up exchange.

Because natural-language branching factor is huge, we do NOT use pure random rollouts.
Instead, simulation uses a *heuristic scoring function* on the state reached after
one move, rather than simulating to a terminal leaf.  This is a standard technique for
language-based adversarial search (analogous to eval functions in chess engines).

=== STATE REPRESENTATION ===

DebateState is a lightweight dataclass carrying:
    - own_claims:       list of propositional atoms this agent has asserted
    - opponent_claims:  list of propositional atoms the opponent has asserted
    - own_kb_size:      number of clauses in this agent's KB (for scoring)
    - contradictions_forced:   int — how many opponent contradictions we have produced
    - contradictions_received: int — how many of our own claims have been contradicted

The heuristic score of a state =
    contradictions_forced − contradictions_received

This is the "performance measure" for the debater agent described in the master prompt:
    "contradictions forced minus contradictions received".

=== MCTS PHASES ===

1. Selection   — traverse tree from root using UCB1 until a non-fully-expanded node
                 (or terminal node) is reached.
2. Expansion   — pick one untried child move, add it as a new Node, apply the move
                 to get the child state.
3. Simulation  — from the new child, score the state using the heuristic (one-step
                 lookahead). No further tree traversal needed for MVP; extending to
                 multi-step rollout is a natural future improvement.
4. Backpropagation — walk back up to root, incrementing visit_count and accumulating
                 value at every ancestor.

=== PUBLIC API ===

    select_best_rebuttal(candidates, current_state, n_simulations)
        → (chosen_str, list[RejectedCandidate])

The caller (tool_executor.py) passes a list of candidate rebuttal strings + the
current debate state.  Each candidate is treated as a "move" (child of the root).
MCTS runs for n_simulations iterations, then returns the candidate with the highest
average score (value / visit_count).  The rejected candidates are also returned
with their scores — this is what the UI's MCTSTracePanel displays.
"""
from __future__ import annotations

import math
import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Optional


UCB1_EXPLORATION_CONSTANT: float = math.sqrt(2)                               


@dataclass
class DebateState:
    """
    A snapshot of the debate at a given point, sufficient for MCTS scoring.

    own_claims:              propositional atom strings this agent has asserted
    opponent_claims:         propositional atom strings the opponent has asserted
    contradictions_forced:   number of opponent contradictions this agent produced
    contradictions_received: number of own contradictions triggered by opponent
    candidate_text:          the rebuttal text this state represents (set on expansion)
    """
    own_claims: list[str] = field(default_factory=list)
    opponent_claims: list[str] = field(default_factory=list)
    contradictions_forced: int = 0
    contradictions_received: int = 0
    candidate_text: str = ""

    def heuristic_score(self) -> float:
        """
        Evaluate this state's desirability for the acting agent.

        Score = contradictions_forced − contradictions_received
                + 0.1 * (own_claims_unique − opponent_claims_unique)

        The small 0.1 term rewards having more distinct claims on the table
        (broader argument coverage), but the contradiction terms dominate —
        matching the project's emphasis on logic over quantity.

        Returns a float so that fractional penalties/bonuses can be added
        cleanly in future without changing callers.
        """
        own_unique = len(set(self.own_claims))
        opp_unique = len(set(self.opponent_claims))
        return (
            float(self.contradictions_forced - self.contradictions_received)
            + 0.1 * float(own_unique - opp_unique)
        )

    def apply_candidate(self, candidate_text: str, simulated_contradictions_forced: int = 0) -> "DebateState":
        """
        Produce a new DebateState representing the result of playing `candidate_text`
        as our next move.

        In MVP (Phase 2), the simulation assumes:
            - We assert the candidate as a new claim.
            - simulated_contradictions_forced is provided by the caller (from a
              heuristic estimate or a real resolution check if available).
            - The opponent does not respond in this one-step lookahead.

        This is deliberately simple — the key value of MCTS here is in comparing
        N candidates against each other using a consistent scoring function,
        not in accurate multi-step prediction.
        """
        next_state = deepcopy(self)
        next_state.own_claims = list(self.own_claims) + [candidate_text]
        next_state.contradictions_forced += simulated_contradictions_forced
        next_state.candidate_text = candidate_text
        return next_state


@dataclass
class Node:
    """
    A node in the MCTS game tree.

    state:         the DebateState at this node
    parent:        parent Node (None for root)
    children:      list of child Nodes (one per tried candidate/move)
    visit_count:   number of times this node was visited across all simulations
    value:         cumulative heuristic score backpropagated through this node
    untried_moves: candidate rebuttal strings not yet expanded from this node
    move:          the candidate text that led from parent to this node
    """
    state: DebateState
    parent: Optional["Node"] = field(default=None, repr=False)
    children: list["Node"] = field(default_factory=list)
    visit_count: int = 0
    value: float = 0.0
    untried_moves: list[str] = field(default_factory=list)
    move: str = ""                                                               

                                                                        
    def ucb1(self, exploration_constant: float = UCB1_EXPLORATION_CONSTANT) -> float:
        """
        Compute the UCB1 score for this node:

            UCB1 = (value / visit_count) + C * sqrt(ln(parent.visit_count) / visit_count)

        The first term is exploitation (high-scoring nodes are preferred).
        The second term is exploration (less-visited nodes get a bonus).

        If visit_count == 0, return +∞ so unvisited nodes are always selected first.
        This guarantees every child is visited at least once before exploitation begins.

        If this node is the root (no parent), exploration term is 0.
        """
        if self.visit_count == 0:
            return float("inf")

        exploitation = self.value / self.visit_count

        if self.parent is None or self.parent.visit_count == 0:
            return exploitation

        exploration = exploration_constant * math.sqrt(
            math.log(self.parent.visit_count) / self.visit_count
        )
        return exploitation + exploration

    def is_fully_expanded(self) -> bool:
        """
        A node is fully expanded when all candidate moves have been tried
        (i.e., every candidate has a corresponding child node).
        """
        return len(self.untried_moves) == 0

    def is_terminal(self) -> bool:
        """
        In this debate context, a node is terminal when it has no children
        AND no untried moves — i.e., it's a leaf with nothing left to explore.
        For MVP, we treat all expanded leaf nodes as terminal (one-step lookahead).
        """
        return self.is_fully_expanded() and len(self.children) == 0

    def best_child(self, exploration_constant: float = UCB1_EXPLORATION_CONSTANT) -> "Node":
        """
        Return the child with the highest UCB1 score.
        Used during Selection phase.
        """
        return max(self.children, key=lambda c: c.ucb1(exploration_constant))

    def best_child_by_visits(self) -> "Node":
        """
        Return the child with the most visits (highest confidence).
        Used at the END of MCTS to pick the final answer —
        visit count is more robust than raw value for the final selection.
        """
        return max(self.children, key=lambda c: c.visit_count)


@dataclass
class RejectedCandidate:
    """
    A non-chosen rebuttal candidate with its MCTS score.
    Returned alongside the winner by select_best_rebuttal() for the UI's
    MCTSTracePanel ("show your work" visualisation).
    """
    text: str
    score: float                                                
    visit_count: int
    raw_value: float                                                


class MCTS:
    """
    Monte Carlo Tree Search for rebuttal selection.

    Usage:
        mcts = MCTS(n_simulations=50)
        chosen, rejected = mcts.select_best_rebuttal(candidates, current_state)
    """

    def __init__(self, n_simulations: int = 50, exploration_constant: float = UCB1_EXPLORATION_CONSTANT):
        self.n_simulations = n_simulations
        self.exploration_constant = exploration_constant

                                                                        
    def select(self, node: Node) -> Node:
        """
        Traverse the tree from `node` downward using UCB1 until we reach
        a node that is either:
            (a) not fully expanded — it has untried moves, so we should expand it, or
            (b) terminal — no children and no untried moves.

        At each step, follow the child with the highest UCB1 score.
        """
        current = node
        while current.is_fully_expanded() and len(current.children) > 0:
            current = current.best_child(self.exploration_constant)
        return current

                                                                        
    def expand(self, node: Node) -> Node:
        """
        Pick one untried move from `node.untried_moves`, remove it from the list,
        create a new child Node with the resulting state, and attach it.

        We pick the first untried move (deterministic order) rather than randomly,
        so that test results are reproducible without seeding.

        Returns the new child node.
        """
        if not node.untried_moves:
            raise ValueError("expand() called on a fully-expanded node")

        move = node.untried_moves.pop(0)                                     
        child_state = node.state.apply_candidate(move)
        child = Node(
            state=child_state,
            parent=node,
            untried_moves=[],                                                         
            move=move,
        )
        node.children.append(child)
        return child

                                                                        
    def simulate(self, node: Node) -> float:
        """
        Evaluate the state at `node` using the heuristic scoring function.

        Design note (from master prompt):
            "Branching factor is language-based" — pure random rollout is impractical.
            We use the state's heuristic_score() as a one-step simulation result.
            This is a standard approximation for domains with large action spaces.

        In a future extension, this could be replaced with a deeper lookahead by
        generating opponent counter-moves and running resolution on them, but for MVP
        the one-step heuristic is both sufficient and more transparent.

        Returns:
            float — the heuristic score of the node's state.
        """
        return node.state.heuristic_score()

                                                                        
    def backpropagate(self, node: Node, result: float) -> None:
        """
        Walk from `node` back up to the root, adding `result` to every
        node's value and incrementing every node's visit_count by 1.

        This propagates the simulation result through all ancestors so that
        UCB1 scores at every level reflect what we've learned about this subtree.
        """
        current: Optional[Node] = node
        while current is not None:
            current.visit_count += 1
            current.value += result
            current = current.parent

                                                                        
    def run(self, root: Node) -> None:
        """
        Execute the MCTS main loop for self.n_simulations iterations.
        Each iteration runs: Select → Expand (if possible) → Simulate → Backpropagate.
        """
        for _ in range(self.n_simulations):
                                                          
            node = self.select(root)

                                                                                     
            if node.untried_moves:
                node = self.expand(node)

                                                                           
            result = self.simulate(node)

                                                                          
            self.backpropagate(node, result)

                                                                        
    def select_best_rebuttal(
        self,
        candidates: list[str],
        current_state: DebateState,
    ) -> tuple[str, list[RejectedCandidate]]:
        """
        Run MCTS to select the best rebuttal from the candidate list.

        Args:
            candidates:    List of candidate rebuttal strings (from the LLM's generate_claim call).
                           Must be non-empty. The LLM generates these; MCTS picks among them.
            current_state: The DebateState at the time of selection.

        Returns:
            (chosen_text, rejected_candidates)
            - chosen_text:       the candidate MCTS judged best
            - rejected_candidates: all others, with their scores, for UI display

        Algorithm:
            1. Build a root Node with current_state and all candidates as untried_moves.
            2. Run MCTS for n_simulations iterations.
            3. Choose the root's child with the highest visit_count (most robust estimate).
            4. Package all other children as RejectedCandidate objects.

        Raises:
            ValueError: if candidates is empty.
        """
        if not candidates:
            raise ValueError("select_best_rebuttal requires at least one candidate")

                                                       
        seen: set[str] = set()
        unique_candidates: list[str] = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                unique_candidates.append(c)

                                                                      
        root = Node(
            state=deepcopy(current_state),
            untried_moves=list(unique_candidates),
        )

                  
        self.run(root)

                                                                                    
        if not root.children:
            return (
                unique_candidates[0],
                [
                    RejectedCandidate(text=c, score=0.0, visit_count=0, raw_value=0.0)
                    for c in unique_candidates[1:]
                ],
            )

                                                                 
        winner = root.best_child_by_visits()
        chosen_text = winner.move

                                                                  
        rejected: list[RejectedCandidate] = []
        for child in root.children:
            if child.move == chosen_text:
                continue
            avg_score = child.value / child.visit_count if child.visit_count > 0 else 0.0
            rejected.append(
                RejectedCandidate(
                    text=child.move,
                    score=round(avg_score, 4),
                    visit_count=child.visit_count,
                    raw_value=round(child.value, 4),
                )
            )

                                                                                              
        tried_moves = {child.move for child in root.children}
        for cand in unique_candidates:
            if cand not in tried_moves and cand != chosen_text:
                rejected.append(
                    RejectedCandidate(text=cand, score=0.0, visit_count=0, raw_value=0.0)
                )

        return chosen_text, rejected


def select_best_rebuttal(
    candidates: list[str],
    current_state: DebateState,
    n_simulations: int = 50,
) -> tuple[str, list[RejectedCandidate]]:
    """
    Module-level wrapper for MCTS.select_best_rebuttal().
    This is the function tool_executor.py will call.
    """
    mcts = MCTS(n_simulations=n_simulations)
    return mcts.select_best_rebuttal(candidates, current_state)
