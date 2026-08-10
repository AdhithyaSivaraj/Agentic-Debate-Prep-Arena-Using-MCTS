"""
routes_debate.py — FastAPI Endpoint Route Definitions for Debate Arena

API Endpoints:
- POST /start-debate        { topic: str, max_turns?: int } → generates fact base on-demand, returns debate_id
- POST /next-turn           { debate_id: str }               → advances debate by 1 turn, returns Turn object
- GET  /transcript/{debate_id}                                → full turn history & summary when complete
- GET  /mcts-trace/{debate_id}/{turn_number}                  → detailed candidate scores for that turn
- GET  /summary/{debate_id}                                   → detailed debate summary & verdict
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
import numpy as np

from agents.gemini_agent import GeminiAgent
from agents.nemotron_agent import NemotronAgent
from agents.nvidia_agent import NvidiaAgent
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MODEL_FALLBACKS, OPENROUTER_API_KEY, NVIDIA_API_KEY, NVIDIA_BASE_URL, GROQ_API_KEY, GROQ_BASE_URL, MCTS_N_SIMULATIONS, FACT_BASE_SIZE
from core.fact_generation import (
    FactRecord,
    extract_fact_texts,
    extract_valid_clauses,
    generate_fact_base,
    generate_fact_base_openai,
)
from core.topic_knowledge import get_topic_grounded_facts, get_targeted_rebuttal
from core.mcts import DebateState
from core.retrieval import FactIndex, build_index, clear_index, make_nemotron_embed_fn
from models.schemas import (
    Claim,
    ContradictionResult,
    CorneringPoint,
    DebateSession,
    DebateSummary,
    MCTSTrace,
    NextTurnRequest,
    RejectedCandidate,
    StartDebateRequest,
    StartDebateResponse,
    Turn,
)
from tools.tool_executor import ExecutorContext, parse_propositional_form

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for active debate sessions (garbage collected per session)
DEBATE_SESSIONS: dict[str, dict[str, Any]] = {}


def _fallback_embed_fn(texts: list[str]) -> np.ndarray:
    """Local deterministic fallback embedding function when OpenRouter key is not set."""
    vecs = []
    for text in texts:
        v = np.zeros(16, dtype=float)
        for i, char in enumerate(text.lower()):
            v[ord(char) % 16] += 1.0 / (i + 1)
        norm = np.linalg.norm(v)
        if norm > 0:
            v /= norm
        vecs.append(v)
    return np.array(vecs)


def _generate_fallback_facts(topic: str) -> list[FactRecord]:
    """Generate structured fallback facts dynamically for the exact topic given."""
    return get_topic_grounded_facts(topic)


@router.post("/start-debate", response_model=StartDebateResponse, status_code=status.HTTP_201_CREATED)
def start_debate(req: StartDebateRequest) -> StartDebateResponse:
    """
    Initialize a new debate session for a given topic.
    Generates fact base on-demand for this topic, builds semantic index, and initializes debater agents.
    Clears any prior global index to ensure complete session isolation.
    """
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    debate_id = uuid.uuid4().hex[:8]

    # Always clear existing retrieval index to ensure clean, on-demand index creation per topic
    clear_index()

    proposer_model = req.proposer_model or "gemini-3.6-flash"
    opponent_model = req.opponent_model or "gemini-3.6-flash"

    # Generate fact base on-demand for this topic using selected proposer model provider
    facts: list[FactRecord] = []

    if "versatile" in proposer_model or "instant" in proposer_model or "groq" in proposer_model.lower():
        if GROQ_API_KEY:
            try:
                facts = generate_fact_base_openai(topic, GROQ_API_KEY, GROQ_BASE_URL, proposer_model, n_facts=FACT_BASE_SIZE)
            except Exception as e:
                logger.warning(f"Groq fact generation failed ({e}). Trying fallback...")

    elif "/" in proposer_model or "llama" in proposer_model.lower() or "nemotron" in proposer_model.lower():
        if NVIDIA_API_KEY:
            try:
                facts = generate_fact_base_openai(topic, NVIDIA_API_KEY, NVIDIA_BASE_URL, proposer_model, n_facts=FACT_BASE_SIZE)
            except Exception as e:
                logger.warning(f"NVIDIA fact generation failed ({e}). Trying fallback...")

    if not facts and GEMINI_API_KEY:
        for model_name in GEMINI_MODEL_FALLBACKS:
            try:
                facts = generate_fact_base(topic, GEMINI_API_KEY, n_facts=FACT_BASE_SIZE, model_name=model_name)
                if facts:
                    break
            except Exception as e:
                logger.warning(f"Gemini fact generation failed with '{model_name}' ({e}). Trying next model...")
                continue

    if not facts:
        facts = _generate_fallback_facts(topic)

    fact_texts = extract_fact_texts(facts)
    valid_clauses = extract_valid_clauses(facts)

    # Build embedding function & FactIndex on-demand for this topic
    if OPENROUTER_API_KEY:
        embed_fn = make_nemotron_embed_fn(OPENROUTER_API_KEY)
    else:
        embed_fn = _fallback_embed_fn

    try:
        fact_index = build_index(fact_texts, embed_fn)
    except Exception as e:
        logger.warning(f"Embedding index build failed with embed_fn ({e}). Using local fallback.")
        fact_index = build_index(fact_texts, _fallback_embed_fn)
        embed_fn = _fallback_embed_fn

    # Helper to instantiate agent based on selected model
    def _create_agent(agent_id: str, role: str, model_name: str):
        if "/" in model_name or "llama" in model_name.lower() or "deepseek" in model_name.lower() or "nemotron" in model_name.lower():
            return NvidiaAgent(agent_id=agent_id, role=role, model_name=model_name)
        return GeminiAgent(agent_id=agent_id, role=role)

    # Initialize agents with user-selected models
    proposer_model = req.proposer_model or "gemini-3.6-flash"
    opponent_model = req.opponent_model or "gemini-3.6-flash"

    agent_a = _create_agent("agent_a", "proposer", proposer_model)
    agent_b = _create_agent("agent_b", "opponent", opponent_model)

    # Seed knowledge bases with initial clauses
    for clause in valid_clauses[:len(valid_clauses) // 2]:
        agent_a.kb.tell(clause)
    for clause in valid_clauses[len(valid_clauses) // 2:]:
        agent_b.kb.tell(clause)

    max_turns = req.max_turns if req.max_turns and req.max_turns > 0 else 20

    # Save session state (scoped to debate_id, vanishes when session is cleared)
    DEBATE_SESSIONS[debate_id] = {
        "debate_id": debate_id,
        "topic": topic,
        "max_turns": max_turns,
        "proposer_model": proposer_model,
        "opponent_model": opponent_model,
        "fact_records": facts,
        "fact_texts": fact_texts,
        "fact_index": fact_index,
        "embed_fn": embed_fn,
        "agent_a": agent_a,
        "agent_b": agent_b,
        "turns": [],
        "status": "running",
        "debate_state": DebateState(),
        "summary": None,
    }

    print(f"\n==================================================", flush=True)
    print(f" 🎬 DEBATE INITIALIZED: '{topic}' (ID: {debate_id}, Max Turns: {max_turns})", flush=True)
    print(f" 🤖 Agent A: {proposer_model} | Agent B: {opponent_model}", flush=True)
    print(f" 📚 Grounded Fact Base: {len(fact_texts)} facts loaded on-demand", flush=True)
    print(f"==================================================\n", flush=True)

    return StartDebateResponse(
        debate_id=debate_id,
        topic=topic,
        max_turns=max_turns,
        proposer_model=proposer_model,
        opponent_model=opponent_model,
        fact_base_count=len(fact_texts),
        message=f"Debate initialized on '{topic}' ({max_turns} turns limit) with {len(fact_texts)} grounded facts.",
    )


@router.post("/next-turn", response_model=Turn)
def next_turn(req: NextTurnRequest) -> Turn:
    """
    Advance the debate by one turn.
    Alternates between Agent A (Gemini) and Agent B (Nemotron).
    Applies resolution contradiction detection and MCTS move selection.
    Automatically generates debate summary when max_turns is reached.
    """
    debate_id = req.debate_id
    if debate_id not in DEBATE_SESSIONS:
        raise HTTPException(status_code=404, detail=f"Debate session '{debate_id}' not found")

    session = DEBATE_SESSIONS[debate_id]
    max_turns = session.get("max_turns", 20)

    if session["status"] == "complete" or len(session["turns"]) >= max_turns:
        session["status"] = "complete"
        raise HTTPException(
            status_code=400,
            detail=f"Debate session '{debate_id}' has reached the maximum turn limit ({max_turns} turns)."
        )

    turns: list[Turn] = session["turns"]
    turn_number = len(turns) + 1

    # Determine speaker
    is_agent_a = (turn_number % 2 != 0)
    current_agent = session["agent_a"] if is_agent_a else session["agent_b"]
    other_agent = session["agent_b"] if is_agent_a else session["agent_a"]

    opponent_last_claim = turns[-1].claim.text if turns else None

    # Construct execution context
    ctx = ExecutorContext(
        agent_kb=current_agent.kb,
        opponent_kb=other_agent.kb,
        embed_fn=session["embed_fn"],
        fact_index=session["fact_index"],
        debate_state=session["debate_state"],
        n_simulations=MCTS_N_SIMULATIONS,
        agent_id=current_agent.agent_id,
    )

    # Run agent turn
    res = current_agent.run_turn(
        topic=session["topic"],
        opponent_last_claim=opponent_last_claim,
        turn_number=turn_number,
        ctx=ctx,
    )

    # Build Pydantic models for response
    contradiction_data = res.get("contradiction_result", {})
    contradiction_result = ContradictionResult(
        found=contradiction_data.get("found", False),
        conflicting_clauses=contradiction_data.get("conflicting_clauses", []),
        proof_steps=contradiction_data.get("proof_steps", []),
    )

    mcts_data = res.get("mcts_trace")
    mcts_trace = None
    if mcts_data and isinstance(mcts_data, dict):
        rejected_objs = [
            RejectedCandidate(
                text=r.get("text", ""),
                score=float(r.get("score", 0.0)),
                visit_count=int(r.get("visit_count", 0)),
            )
            for r in mcts_data.get("rejected_candidates", [])
        ]
        mcts_trace = MCTSTrace(
            chosen_rebuttal=mcts_data.get("chosen_rebuttal", ""),
            chosen_score=float(mcts_data.get("chosen_score", 0.0)),
            rejected_candidates=rejected_objs,
            n_simulations=int(mcts_data.get("n_simulations", MCTS_N_SIMULATIONS)),
        )

    # Update state score if contradiction found
    if contradiction_result.found:
        if is_agent_a:
            session["debate_state"].contradictions_forced += 1
        else:
            session["debate_state"].contradictions_received += 1

    spoken_text = res.get("claim_text", "")
    chosen_reb = mcts_trace.chosen_rebuttal if mcts_trace else ""
    if is_agent_a:
        if spoken_text:
            session["debate_state"].own_claims.append(spoken_text)
        if chosen_reb:
            session["debate_state"].own_claims.append(chosen_reb)
    else:
        if spoken_text:
            session["debate_state"].opponent_claims.append(spoken_text)
        if chosen_reb:
            session["debate_state"].opponent_claims.append(chosen_reb)

    claim_obj = Claim(
        text=res.get("claim_text", ""),
        speaker=current_agent.agent_id,
        turn_number=turn_number,
        propositional_form=res.get("propositional_form", ""),
        is_contradicted=contradiction_result.found,
    )

    turn_obj = Turn(
        turn_number=turn_number,
        claim=claim_obj,
        contradiction_result=contradiction_result,
        mcts_trace=mcts_trace,
        mode=res.get("mode", "live"),
    )

    turns.append(turn_obj)

    # Check if max turns reached — synthesize final debate summary if so
    if turn_number >= max_turns:
        session["status"] = "complete"
        session["summary"] = _synthesize_debate_summary(session)
        print(f"\n🏆 DEBATE COMPLETE! Summary generated for topic: '{session['topic']}'\n", flush=True)

    # Terminal Log Output for debugging and tagging
    speaker_name = "Agent A (Gemini)" if is_agent_a else "Agent B (Nemotron)"
    print(f"\n--------------------------------------------------", flush=True)
    print(f" 📢 TURN #{turn_number}/{max_turns} | SPEAKER: {speaker_name}", flush=True)
    print(f" 🗣️  Claim: {claim_obj.text}", flush=True)
    print(f" 📐 Clause: {claim_obj.propositional_form}", flush=True)
    print(f" ⚡ Contradiction Found: {contradiction_result.found}", flush=True)
    if mcts_trace:
        print(f" 🌳 MCTS Chosen Rebuttal: {mcts_trace.chosen_rebuttal}", flush=True)
    print(f"--------------------------------------------------\n", flush=True)

    return turn_obj


def _generate_live_counter_reply(topic: str, attack_claim: str, defending_role: str) -> str:
    """
    Call Gemini to generate a concrete, specific counter-argument for a given attack claim.
    Returns a real debate point the defender can fire back with — NOT a vague strategy description.
    Falls back to a generic reply if the API call fails.
    """
    if not GEMINI_API_KEY:
        return None

    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)

    prompt = (
        f"Debate topic: '{topic}'\n"
        f"The {('opponent' if defending_role == 'proposer' else 'proposer')} just said:\n"
        f"\"{attack_claim}\"\n\n"
        f"You are coaching the {defending_role}. Write ONE specific, concrete counter-argument they can say "
        f"to directly refute this attack. The counter-argument must:\n"
        f"- Be a specific factual or logical claim, not a vague strategy\n"
        f"- Directly address the attack's core premise\n"
        f"- Be 1-2 sentences, confident and direct\n"
        f"- Read like something a skilled debater would actually say aloud\n"
        f"Output only the counter-argument text, nothing else."
    )

    for model_name in GEMINI_MODEL_FALLBACKS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text:
                return text
        except Exception:
            continue

    return None


def _synthesize_debate_summary(session: dict[str, Any]) -> DebateSummary:
    """Generate structured DebateSummary object of completed debate session."""
    topic = session["topic"]
    turns: list[Turn] = session["turns"]
    total_turns = len(turns)
    contradictions = sum(1 for t in turns if t.contradiction_result and t.contradiction_result.found)

    state: DebateState = session["debate_state"]
    score_a = state.heuristic_score()

    if score_a > 0:
        winner = "Agent A (Proposer)"
        reasoning = f"Agent A established stronger logical grounding on '{topic}' and maintained argument consistency."
    elif score_a < 0:
        winner = "Agent B (Opponent)"
        reasoning = f"Agent B successfully challenged core premises on '{topic}' and presented compelling counter-evidence."
    else:
        winner = "Draw / Balanced"
        reasoning = f"Both agents maintained strong logical rigor across all turns of the debate on '{topic}'."

    pro_claims = [t.claim.text for t in turns if t.claim.speaker == "agent_a"]
    opp_claims = [t.claim.text for t in turns if t.claim.speaker == "agent_b"]

    cornering_points = []

    # Pick the most impactful attack from each side
    # For opponent's attack: pick the longest/most-developed claim (most likely to corner)
    best_opp_attack = max(opp_claims, key=len) if opp_claims else None
    best_pro_attack = max(pro_claims, key=len) if pro_claims else None

    # Check top Opponent attack against Proposer
    if best_opp_attack:
        reb_b = (
            _generate_live_counter_reply(topic, best_opp_attack, "proposer")
            or get_targeted_rebuttal(topic, best_opp_attack, "proposer")
            or f"Empirical evidence shows this criticism overlooks the core advantage of the proposer's position on {topic}."
        )
        cornering_points.append(
            CorneringPoint(
                point=best_opp_attack,
                speaker="Agent B (Opponent)",
                risk_level="HIGH THREAT",
                why_dangerous=f"Directly challenges the core viability of the proposer's argument on '{topic}'.",
                best_reply=reb_b,
            )
        )

    # Check top Proposer attack against Opponent
    if best_pro_attack:
        reb_a = (
            _generate_live_counter_reply(topic, best_pro_attack, "opponent")
            or get_targeted_rebuttal(topic, best_pro_attack, "opponent")
            or f"This premise relies on ideal conditions that rarely hold in practice, undermining the proposer's case."
        )
        cornering_points.append(
            CorneringPoint(
                point=best_pro_attack,
                speaker="Agent A (Proposer)",
                risk_level="TACTICAL ADVANTAGE",
                why_dangerous=f"Establishes a strong proactive benchmark that puts the opponent on the defensive.",
                best_reply=reb_a,
            )
        )

    if not cornering_points:
        cornering_points = [
            CorneringPoint(
                point=f"Strategic analysis on topic '{topic}'.",
                speaker="Agent B (Opponent)",
                risk_level="HIGH THREAT",
                why_dangerous="Exposes logical weakness if premises lack empirical support.",
                best_reply=f"Ground your response in specific, verifiable facts about '{topic}'.",
            )
        ]

    return DebateSummary(
        debate_id=session["debate_id"],
        topic=topic,
        total_turns=total_turns,
        winner=winner,
        winner_reasoning=reasoning,
        proposer_key_points=pro_claims[:3],
        opponent_key_points=opp_claims[:3],
        total_contradictions=contradictions,
        verdict_statement=f"Debate on '{topic}' complete across {total_turns} turns. Winner: {winner}.",
        cornering_points=cornering_points,
        proposer_full_arguments=pro_claims,
        opponent_full_arguments=opp_claims,
    )


@router.get("/transcript/{debate_id}", response_model=DebateSession)
def get_transcript(debate_id: str) -> DebateSession:
    """Retrieve full transcript and session state for a given debate_id."""
    if debate_id not in DEBATE_SESSIONS:
        raise HTTPException(status_code=404, detail=f"Debate session '{debate_id}' not found")

    session = DEBATE_SESSIONS[debate_id]
    return DebateSession(
        debate_id=session["debate_id"],
        topic=session["topic"],
        max_turns=session.get("max_turns", 20),
        proposer_model=session.get("proposer_model", "gemini-3.6-flash"),
        opponent_model=session.get("opponent_model", "gemini-3.6-flash"),
        fact_base=session["fact_texts"],
        turns=session["turns"],
        status=session["status"],
        summary=session.get("summary"),
    )


@router.get("/mcts-trace/{debate_id}/{turn_number}", response_model=MCTSTrace)
def get_mcts_trace(debate_id: str, turn_number: int) -> MCTSTrace:
    """Retrieve MCTS reasoning trace for a specific turn."""
    if debate_id not in DEBATE_SESSIONS:
        raise HTTPException(status_code=404, detail=f"Debate session '{debate_id}' not found")

    session = DEBATE_SESSIONS[debate_id]
    turns: list[Turn] = session["turns"]

    for turn in turns:
        if turn.turn_number == turn_number:
            if turn.mcts_trace:
                return turn.mcts_trace
            raise HTTPException(status_code=404, detail=f"MCTS was not invoked on turn {turn_number}")

    raise HTTPException(status_code=404, detail=f"Turn {turn_number} not found in debate '{debate_id}'")


@router.get("/summary/{debate_id}", response_model=DebateSummary)
def get_debate_summary(debate_id: str) -> DebateSummary:
    """Retrieve detailed debate summary and verdict after completion."""
    if debate_id not in DEBATE_SESSIONS:
        raise HTTPException(status_code=404, detail=f"Debate session '{debate_id}' not found")

    session = DEBATE_SESSIONS[debate_id]
    session["status"] = "complete"  # Mark debate as completed when verdict/summary is generated
    if not session.get("summary"):
        session["summary"] = _synthesize_debate_summary(session)
    return session["summary"]
