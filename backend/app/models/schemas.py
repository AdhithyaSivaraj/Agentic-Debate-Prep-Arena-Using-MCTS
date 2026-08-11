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
    speaker: str                                          
    turn_number: int
    propositional_form: str                                                            
    is_contradicted: bool = False


class ContradictionResult(BaseModel):
    """Contradiction detection result from the resolution algorithm."""
    found: bool
    conflicting_clauses: list[list[str]]                               
    proof_steps: list[str]                                                        


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
    mcts_trace: MCTSTrace | None = None                                          
    mode: str = "live"                                                                           


class CorneringPoint(BaseModel):
    """A high-risk argument made during debate that could corner a debater, plus its best counter-reply and escape route."""
    point: str
    speaker: str                                                              
    risk_level: str                                                                            
    why_dangerous: str
    best_reply: str
    escape_route: str | None = None


class DebateSummary(BaseModel):
    """Executive summary, tactical cornering analysis, and verdict report authored by Proposer Agent."""
    debate_id: str
    topic: str
    total_turns: int
    winner: str                                                                                     
    winner_reasoning: str
    proposer_key_points: list[str]
    opponent_key_points: list[str]
    total_contradictions: int
    verdict_statement: str
    proposer_cornered_analysis: str = ""                                              
    opponent_cornered_analysis: str = ""                                    
    opponent_escape_route: str = ""                                                           
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
    fact_base: list[str]                                          
    turns: list[Turn] = []
    status: str = "not_started"                                           
    summary: DebateSummary | None = None
