"""
schemas.py — Pydantic models for API request/response validation.
"""
from __future__ import annotations
from pydantic import BaseModel
from typing import Any


class StartDebateRequest(BaseModel):
    """Request model for POST /start-debate."""
    topic: str
    max_turns: int = 20
    proposer_model: str = "gemini-3.6-flash"
    opponent_model: str = "gemini-3.6-flash"


class StartDebateResponse(BaseModel):
    """Response model for POST /start-debate."""
    debate_id: str
    topic: str
    max_turns: int = 20
    proposer_model: str = "gemini-3.6-flash"
    opponent_model: str = "gemini-3.6-flash"
    fact_base_count: int
    message: str


class NextTurnRequest(BaseModel):
    """Request model for POST /next-turn."""
    debate_id: str


class Claim(BaseModel):
    """A single claim made by one agent in one turn."""
    text: str
    speaker: str                  # "agent_a" or "agent_b"
    turn_number: int
    propositional_form: str       # normalized clause form (e.g., "Exams → StressHigh")
    is_contradicted: bool = False


class ContradictionResult(BaseModel):
    """Contradiction detection result from the resolution algorithm."""
    found: bool
    conflicting_clauses: list[list[str]]  # list of clause-string pairs
    proof_steps: list[str]                # human-readable derivation trace for UI


class RejectedCandidate(BaseModel):
    """A non-chosen rebuttal candidate from MCTS."""
    text: str
    score: float
    visit_count: int


class MCTSTrace(BaseModel):
    """Full MCTS trace for one turn — for the UI's 'show your work' panel."""
    chosen_rebuttal: str
    chosen_score: float
    rejected_candidates: list[RejectedCandidate]
    n_simulations: int


class Turn(BaseModel):
    """One complete debate turn."""
    turn_number: int
    claim: Claim
    contradiction_result: ContradictionResult
    mcts_trace: MCTSTrace | None = None  # None if MCTS was not invoked this turn
    mode: str = "live"                   # "live" (real LLM API) or "fallback" (offline fallback)


class CorneringPoint(BaseModel):
    """A high-risk argument made during debate that could corner a debater, plus its best counter-reply."""
    point: str
    speaker: str                 # "Agent A (Proposer)" | "Agent B (Opponent)"
    risk_level: str              # "CRITICAL VULNERABILITY" | "HIGH THREAT" | "MODERATE THREAT"
    why_dangerous: str
    best_reply: str


class DebateSummary(BaseModel):
    """Executive summary, tactical coaching, and verdict report of a completed debate."""
    debate_id: str
    topic: str
    total_turns: int
    winner: str                    # "Agent A (Proposer)" | "Agent B (Opponent)" | "Draw / Balanced"
    winner_reasoning: str
    proposer_key_points: list[str]
    opponent_key_points: list[str]
    total_contradictions: int
    verdict_statement: str
    cornering_points: list[CorneringPoint] = []
    proposer_full_arguments: list[str] = []
    opponent_full_arguments: list[str] = []


class DebateSession(BaseModel):
    """Full state of one debate session (in-memory, keyed by debate_id)."""
    debate_id: str
    topic: str
    max_turns: int = 20
    proposer_model: str = "gemini-3.6-flash"
    opponent_model: str = "gemini-3.6-flash"
    fact_base: list[str]          # raw fact strings for reference
    turns: list[Turn] = []
    status: str = "not_started"   # "not_started" | "running" | "complete"
    summary: DebateSummary | None = None
