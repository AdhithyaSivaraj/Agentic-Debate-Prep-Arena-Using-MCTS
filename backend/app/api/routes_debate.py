"""
routes_debate.py — FastAPI Endpoint Route Definitions for Debate Arena

API Endpoints:
- POST /start-debate        { topic, max_turns?, proposer_model?, opponent_model? }
                            → generates the fact base, seeds both KBs, returns debate_id
- POST /next-turn           { debate_id: str }   → advances debate by 1 turn, returns Turn
- GET  /transcript/{debate_id}                    → full turn history & summary when complete
- GET  /mcts-trace/{debate_id}/{turn_number}      → candidate scores for that turn
- GET  /summary/{debate_id}                       → debate summary & verdict (built on first request)
"""
from __future__ import annotations

import logging
import uuid
from collections import Counter
from typing import Any

from fastapi import APIRouter, HTTPException, status

from agents.debater_agent import DebaterAgent
from config import FACT_BASE_SIZE, MCTS_N_SIMULATIONS
from core.fact_generation import DebateFrame, extract_fact_texts, frame_debate, generate_fact_base
from core.mcts import DebateState
from core.resolution import Clause, atoms_of, check_contradiction, parse_propositional_form
from core.retrieval import build_index, clear_index, hashed_bow_embed
from llm_client import LLMUnavailable, clean_claim_text, complete_any, humanize_logic, parse_json_payload
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
from tools.tool_executor import ExecutorContext

logger = logging.getLogger(__name__)

router = APIRouter()

DEBATE_SESSIONS: dict[str, dict[str, Any]] = {}


def _get_session(debate_id: str) -> dict[str, Any]:
    if debate_id not in DEBATE_SESSIONS:
        raise HTTPException(status_code=404, detail=f"Debate session '{debate_id}' not found")
    return DEBATE_SESSIONS[debate_id]


@router.post("/start-debate", response_model=StartDebateResponse, status_code=status.HTTP_201_CREATED)
def start_debate(req: StartDebateRequest) -> StartDebateResponse:
    """
    Initialize a new debate session for a given topic.
    Generates the fact base, builds the retrieval index, and seeds each agent's KB
    with the facts on its side of the resolution.
    """
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    frame = frame_debate(topic)
    try:
        facts, fact_model = generate_fact_base(topic, n_facts=FACT_BASE_SIZE, frame=frame)
    except LLMUnavailable as e:
        logger.error(f"Fact base generation failed for '{topic}': {e}")
        raise HTTPException(
            status_code=503,
            detail="Could not generate a fact base: no LLM provider responded. Check the API keys in backend/.env.",
        )

    debate_id = uuid.uuid4().hex[:8]
    clear_index()
    fact_texts = extract_fact_texts(facts)
    fact_index = build_index(fact_texts, hashed_bow_embed)

    agent_a = DebaterAgent("agent_a", "proposer", req.proposer_model, facts, frame)
    agent_b = DebaterAgent("agent_b", "opponent", req.opponent_model, facts, frame)
    for agent in (agent_a, agent_b):
        skipped = [
            f.propositional for f in agent.side_facts
            if f.clause is not None and not agent.kb.tell_if_consistent(f.clause, human_readable=f.text)
        ]
        if skipped:
            logger.info(f"{agent.agent_id}: skipped facts that would make its KB inconsistent: {skipped}")

    max_turns = req.max_turns if req.max_turns and req.max_turns > 0 else 20
    vocabulary = {a for f in facts if f.clause is not None for a in atoms_of(f.clause)}

    DEBATE_SESSIONS[debate_id] = {
        "debate_id": debate_id,
        "topic": topic,
        "max_turns": max_turns,
        "proposer_model": req.proposer_model,
        "opponent_model": req.opponent_model,
        "fact_model": fact_model,
        "frame": frame,
        "fact_records": facts,
        "fact_texts": fact_texts,
        "fact_index": fact_index,
        "embed_fn": hashed_bow_embed,
        "vocabulary": vocabulary,
        "agent_a": agent_a,
        "agent_b": agent_b,
        "turns": [],
        "status": "running",
        "debate_state": DebateState(),
        "summary": None,
    }

    print(f"\n==================================================", flush=True)
    print(f" 🎬 DEBATE INITIALIZED: '{topic}' (ID: {debate_id}, Max Turns: {max_turns})", flush=True)
    print(f" ⚖️  Resolution: {frame.resolution}", flush=True)
    print(f" 🤖 Agent A: {req.proposer_model} — {frame.proposer_position}", flush=True)
    print(f" 🤖 Agent B: {req.opponent_model} — {frame.opponent_position}", flush=True)
    print(f" 📚 Fact base: {len(fact_texts)} facts, {len(vocabulary)} atoms (via {fact_model})", flush=True)
    print(f"==================================================\n", flush=True)

    return StartDebateResponse(
        debate_id=debate_id,
        topic=topic,
        max_turns=max_turns,
        proposer_model=req.proposer_model,
        opponent_model=req.opponent_model,
        fact_base_count=len(fact_texts),
        resolution=frame.resolution,
        proposer_position=frame.proposer_position,
        opponent_position=frame.opponent_position,
        message=f"Debate initialized on '{topic}' ({max_turns} turns limit) with {len(fact_texts)} generated facts.",
    )


def _target_turn(clause: Clause | None, earlier: list[Turn], background: list[Clause]) -> int | None:
    """
    The most recent earlier turn whose claim, on its own (read with `background` evidence),
    contradicts `clause`. None if no single earlier claim is responsible.
    """
    if clause is None or check_contradiction(background + [clause]).found:
        return None
    for turn in reversed(earlier):
        target = parse_propositional_form(turn.claim.propositional_form)
        if target is not None and check_contradiction(background + [target, clause]).found:
            return turn.turn_number
    return None


def _evidence(agent: DebaterAgent) -> list[Clause]:
    """An agent's KB minus what it has claimed in the debate."""
    return [c for c in agent.kb.get_all_clauses() if c not in agent.claimed_clauses]


def _contradiction(data: dict | None) -> ContradictionResult:
    data = data or {}
    return ContradictionResult(
        found=data.get("found", False),
        conflicting_clauses=[list(pair) for pair in data.get("conflicting_clauses", [])],
        proof_steps=data.get("proof_steps", []),
    )


@router.post("/next-turn", response_model=Turn)
def next_turn(req: NextTurnRequest) -> Turn:
    """
    Advance the debate by one turn. Agent A (proposer) speaks on odd turns, Agent B on even.
    A claim that clashes with the opponent's KB scores for the speaker; a claim that
    contradicts the speaker's own KB scores against them.
    """
    session = _get_session(req.debate_id)
    max_turns = session["max_turns"]

    if session["status"] == "complete" or len(session["turns"]) >= max_turns:
        session["status"] = "complete"
        raise HTTPException(
            status_code=400,
            detail=f"Debate session '{req.debate_id}' has reached the maximum turn limit ({max_turns} turns).",
        )

    turns: list[Turn] = session["turns"]
    turn_number = len(turns) + 1
    is_agent_a = turn_number % 2 != 0
    current_agent: DebaterAgent = session["agent_a"] if is_agent_a else session["agent_b"]
    other_agent: DebaterAgent = session["agent_b"] if is_agent_a else session["agent_a"]
    last_claim = turns[-1].claim if turns else None

    ctx = ExecutorContext(
        agent_kb=current_agent.kb,
        opponent_kb=other_agent.kb,
        embed_fn=session["embed_fn"],
        fact_index=session["fact_index"],
        debate_state=session["debate_state"],
        n_simulations=MCTS_N_SIMULATIONS,
        agent_id=current_agent.agent_id,
        opponent_replies=[f.clause for f in other_agent.side_facts if f.clause is not None],
        vocabulary=session["vocabulary"],
        opponent_claimed_clauses=other_agent.claimed_clauses,
        argued_issues=dict(Counter(t.claim.issue for t in turns if t.claim.issue)),
        recent_atom_counts=dict(Counter(
            a for t in turns[-6:]
            for a in atoms_of(parse_propositional_form(t.claim.propositional_form) or frozenset())
        )),
    )

    res = current_agent.run_turn(
        topic=session["topic"],
        opponent_last_claim=last_claim.text if last_claim else None,
        opponent_last_form=last_claim.propositional_form if last_claim else None,
        turn_number=turn_number,
        ctx=ctx,
        history=[
            f"Turn {t.turn_number} — {'Proposer' if t.claim.speaker == 'agent_a' else 'Opponent'}: {t.claim.text}"
            for t in turns
        ],
    )

    self_result = _contradiction(res["contradiction_result"])
    clash_result = _contradiction(res["clash_result"])

    mcts_trace = None
    mcts_data = res.get("mcts_trace")
    if mcts_data:
        mcts_trace = MCTSTrace(
            chosen_rebuttal=mcts_data["chosen_rebuttal"],
            chosen_propositional_form=mcts_data.get("chosen_propositional_form", ""),
            chosen_score=float(mcts_data.get("chosen_score", 0.0)),
            chosen_visits=int(mcts_data.get("chosen_visits", 0)),
            rejected_candidates=[
                RejectedCandidate(
                    text=r["text"],
                    propositional_form=r.get("propositional_form", ""),
                    score=float(r["score"]),
                    visit_count=int(r["visit_count"]),
                )
                for r in mcts_data.get("rejected_candidates", [])
            ],
            n_simulations=int(mcts_data.get("n_simulations", MCTS_N_SIMULATIONS)),
        )

    state: DebateState = session["debate_state"]
    if clash_result.found:
        if is_agent_a:
            state.contradictions_forced += 1
        else:
            state.contradictions_received += 1
    if self_result.found:
        if is_agent_a:
            state.contradictions_received += 1
        else:
            state.contradictions_forced += 1

    claim_clause = parse_propositional_form(res["propositional_form"])
    claim_obj = Claim(
        text=res["claim_text"],
        speaker=current_agent.agent_id,
        turn_number=turn_number,
        propositional_form=res["propositional_form"],
        issue=res.get("issue", ""),
        is_contradicted=self_result.found,
        refutes_opponent=clash_result.found,
        refutes_turn=_target_turn(
            claim_clause, [t for t in turns if t.claim.speaker == other_agent.agent_id], _evidence(other_agent)
        ) if clash_result.found else None,
        contradicts_turn=_target_turn(
            claim_clause, [t for t in turns if t.claim.speaker == current_agent.agent_id], _evidence(current_agent)
        ) if self_result.found else None,
    )
    turn_obj = Turn(
        turn_number=turn_number,
        claim=claim_obj,
        contradiction_result=self_result,
        clash_result=clash_result,
        mcts_trace=mcts_trace,
        mode=res["mode"],
    )
    turns.append(turn_obj)

    model = res.get("model_used") or ("local fact base" if res["mode"] == "fallback" else current_agent.model_name)
    print(f"\n--------------------------------------------------", flush=True)
    print(f" 📢 TURN #{turn_number}/{max_turns} | Agent {'A' if is_agent_a else 'B'} ({model}) [{res['mode']}]", flush=True)
    print(f" 🗣️  Claim: {claim_obj.text}", flush=True)
    print(f" 📐 Clause: {claim_obj.propositional_form}   (issue: {claim_obj.issue or '-'})", flush=True)
    print(f" ⚡ Refutes opponent: {clash_result.found} | Self-contradiction: {self_result.found}", flush=True)
    if mcts_trace:
        print(f" 🌳 MCTS: score {mcts_trace.chosen_score} over {len(mcts_trace.rejected_candidates)} alternatives", flush=True)
    print(f"--------------------------------------------------\n", flush=True)

    if turn_number >= max_turns:
        session["status"] = "complete"
        print(f"\n🏁 DEBATE REACHED MAX TURNS ({turn_number}/{max_turns}) for topic: '{session['topic']}'\n", flush=True)

    return turn_obj


PLAIN_ENGLISH = (
    "Write plain English only: never use CamelCase identifiers or logic symbols (→, ¬, ∨)."
)


def _sides(frame: DebateFrame) -> str:
    return f"Resolution: '{frame.resolution}'\nProposer: {frame.proposer_position}\nOpponent: {frame.opponent_position}"


def _counter_reply(
    frame: DebateFrame, attack_claim: str, defending_role: str, model_hint: str | None, vocabulary: set[str]
) -> str | None:
    """Ask an LLM for one concrete counter-argument to `attack_claim`; None if no provider responds."""
    attacker = "opponent" if defending_role == "proposer" else "proposer"
    prompt = (
        f"{_sides(frame)}\n\n"
        f"The {attacker} just said:\n\"{attack_claim}\"\n\n"
        f"You are coaching the {defending_role}, whose position is: "
        f"{frame.proposer_position if defending_role == 'proposer' else frame.opponent_position} Write ONE specific, concrete "
        f"counter-argument they can say aloud that refutes this attack while staying on their side. It must be a "
        f"factual or logical claim (not a strategy), address the attack's core premise, and be 1-2 confident "
        f"sentences. {PLAIN_ENGLISH} Output only the counter-argument text."
    )
    try:
        text, _ = complete_any(model_hint, "You are an expert debate coach.", prompt, timeout=15.0)
        return humanize_logic(clean_claim_text(text), vocabulary) or None
    except LLMUnavailable as e:
        logger.warning(f"Counter reply generation failed ({str(e)[:200]}).")
        return None


def _summary_debrief(
    frame: DebateFrame, turns: list[Turn], proposer_model: str, winner: str, proof_summary: str, vocabulary: set[str]
) -> dict[str, Any]:
    """
    Ask the Proposer's LLM for the post-debate debrief, grounded in the transcript and the
    resolution results. Returns {} if unavailable or unparseable.
    """
    def proof_note(t: Turn) -> str:
        notes = []
        if t.claim.refutes_opponent:
            notes.append("proved a refutation of the other side")
        if t.claim.is_contradicted:
            notes.append("proved a self-contradiction")
        return f"  [{'; '.join(notes)}]" if notes else ""

    history = "\n".join(
        f"Turn {t.turn_number} — {'Proposer' if t.claim.speaker == 'agent_a' else 'Opponent'}: "
        f"{t.claim.text}{proof_note(t)}"
        for t in turns
    )
    prompt = (
        f"{_sides(frame)}\n\n"
        f"Transcript (bracketed notes are results from a resolution theorem prover):\n{history}\n\n"
        f"Prover results: {proof_summary}\nWinner by those results: {winner}.\n\n"
        f"Write the post-debate debrief. Rules:\n"
        f"- Base every statement on the transcript and prover results above; do not claim any contradiction, "
        f"concession or evidence that is not there.\n"
        f"- Keep each side on its own position: Proposer advice must support the resolution, Opponent advice "
        f"must oppose it.\n"
        f"- Every advice field is an exact sentence a debater could say aloud — not meta-advice like "
        f"'emphasize costs'.\n"
        f"- {PLAIN_ENGLISH}\n\n"
        f"Output a JSON object with exactly these keys:\n"
        f'  "verdict_statement": 2 sentences on why the result came out as it did,\n'
        f'  "proposer_toughest_attack": the Opponent\'s strongest claim against the Proposer (quote or close paraphrase),\n'
        f'  "proposer_defense": what the Proposer should say to answer it,\n'
        f'  "opponent_trap": the Proposer argument the Opponent struggled most to answer,\n'
        f'  "opponent_escape_route": what the Opponent should say to escape that trap,\n'
        f'  "key_proposer_points": [2-3 of the Proposer\'s strongest arguments],\n'
        f'  "key_opponent_points": [2-3 of the Opponent\'s strongest arguments]\n'
    )
    try:
        raw, _ = complete_any(proposer_model, "You are a debate analyst. Output JSON only.", prompt, json_mode=True, timeout=25.0)
        parsed = parse_json_payload(raw)
    except (LLMUnavailable, ValueError) as e:
        logger.warning(f"Summary debrief failed ({str(e)[:200]}).")
        return {}
    if not isinstance(parsed, dict) or not parsed.get("proposer_toughest_attack"):
        return {}

    def clean(value: Any) -> Any:
        if isinstance(value, list):
            return [humanize_logic(str(v), vocabulary) for v in value if str(v).strip()]
        return humanize_logic(str(value), vocabulary) if value else ""

    return {k: clean(v) for k, v in parsed.items()}


def _strongest_claim(turns: list[Turn], speaker: str) -> Turn | None:
    """The speaker's most damaging claim: prefer refutations of the opponent, then the longest claim."""
    own = [t for t in turns if t.claim.speaker == speaker]
    if not own:
        return None
    return max(own, key=lambda t: (t.claim.refutes_opponent, len(t.claim.text)))


def _next_reply(turns: list[Turn], after: Turn) -> str | None:
    """The other side's actual reply to a turn, if one was made."""
    for t in turns:
        if t.turn_number == after.turn_number + 1:
            return t.claim.text
    return None


def _cornering_point(
    frame: DebateFrame, turns: list[Turn], attack: Turn, session: dict[str, Any]
) -> CorneringPoint | None:
    """Attack → the defender's best reply → the attacker's comeback, each argued from the right side."""
    by_proposer = attack.claim.speaker == "agent_a"
    attacker_role, defender_role = ("proposer", "opponent") if by_proposer else ("opponent", "proposer")
    attacker_model = session["proposer_model"] if by_proposer else session["opponent_model"]
    defender_model = session["opponent_model"] if by_proposer else session["proposer_model"]
    vocabulary = session["vocabulary"]

    reply = _counter_reply(frame, attack.claim.text, defender_role, defender_model, vocabulary) or _next_reply(turns, attack)
    if not reply:
        return None
    defender_kb = "Opponent's" if by_proposer else "Proposer's"
    return CorneringPoint(
        point=attack.claim.text,
        speaker="Agent A (Proposer)" if by_proposer else "Agent B (Opponent)",
        risk_level="HIGH THREAT" if attack.claim.refutes_opponent else "TACTICAL CORNER",
        why_dangerous=(
            f"Resolution proved this claim inconsistent with the {defender_kb} committed positions."
            if attack.claim.refutes_opponent
            else f"The {attacker_role.capitalize()}'s most developed attack; no formal contradiction was proven."
        ),
        best_reply=reply,
        escape_route=_counter_reply(frame, reply, attacker_role, attacker_model, vocabulary),
    )


def _synthesize_debate_summary(session: dict[str, Any]) -> DebateSummary:
    """Build the DebateSummary: the verdict comes from resolution results, the prose from the Proposer's LLM."""
    topic = session["topic"]
    turns: list[Turn] = session["turns"]

    def counts(speaker: str) -> tuple[int, int]:
        own = [t for t in turns if t.claim.speaker == speaker]
        return sum(t.claim.refutes_opponent for t in own), sum(t.claim.is_contradicted for t in own)

    a_refutes, a_self = counts("agent_a")
    b_refutes, b_self = counts("agent_b")
    state: DebateState = session["debate_state"]
    score_a = state.contradictions_forced - state.contradictions_received

    if score_a > 0:
        winner = "Agent A (Proposer)"
    elif score_a < 0:
        winner = "Agent B (Opponent)"
    else:
        winner = "Draw / Balanced"
    proof_summary = (
        f"Agent A (Proposer) proved {a_refutes} refutation(s) of the Opponent and {a_self} self-contradiction(s); "
        f"Agent B (Opponent) proved {b_refutes} refutation(s) of the Proposer and {b_self} self-contradiction(s)."
    )
    reasoning = f"{proof_summary} Net logic score for Agent A: {score_a:+d}."

    pro_claims = [t.claim.text for t in turns if t.claim.speaker == "agent_a"]
    opp_claims = [t.claim.text for t in turns if t.claim.speaker == "agent_b"]
    frame: DebateFrame = session["frame"]
    debrief = _summary_debrief(frame, turns, session["proposer_model"], winner, proof_summary, session["vocabulary"])

    best_opp = _strongest_claim(turns, "agent_b")
    best_pro = _strongest_claim(turns, "agent_a")
    cornering_points = [
        cp for cp in (
            _cornering_point(frame, turns, best_opp, session) if best_opp else None,
            _cornering_point(frame, turns, best_pro, session) if best_pro else None,
        ) if cp
    ]

    def attack_and_answer(attack: str, answer: str) -> str:
        return f"Attack: \"{attack}\"\nDefense: \"{answer}\"" if attack and answer else attack

    if debrief:
        proposer_analysis = attack_and_answer(debrief.get("proposer_toughest_attack", ""), debrief.get("proposer_defense", ""))
        opponent_trap = debrief.get("opponent_trap", "")
        opponent_escape = debrief.get("opponent_escape_route", "")
    else:
        proposer_analysis = f"Attack: \"{best_opp.claim.text}\"" if best_opp else ""
        opponent_trap = f"\"{best_pro.claim.text}\"" if best_pro else ""
        opponent_escape = ""

    summary_obj = DebateSummary(
        debate_id=session["debate_id"],
        topic=topic,
        total_turns=len(turns),
        winner=winner,
        winner_reasoning=reasoning,
        proposer_key_points=debrief.get("key_proposer_points") or pro_claims[:3],
        opponent_key_points=debrief.get("key_opponent_points") or opp_claims[:3],
        total_contradictions=a_refutes + a_self + b_refutes + b_self,
        verdict_statement=debrief.get("verdict_statement")
        or f"Debate on '{topic}' concluded after {len(turns)} turns. Winner: {winner}.",
        proposer_cornered_analysis=proposer_analysis,
        opponent_cornered_analysis=opponent_trap,
        opponent_escape_route=opponent_escape,
        cornering_points=cornering_points,
        proposer_full_arguments=pro_claims,
        opponent_full_arguments=opp_claims,
    )
    session["summary"] = summary_obj
    return summary_obj


@router.get("/transcript/{debate_id}", response_model=DebateSession)
def get_transcript(debate_id: str) -> DebateSession:
    """Retrieve full transcript and session state for a given debate_id."""
    session = _get_session(debate_id)
    return DebateSession(
        debate_id=session["debate_id"],
        topic=session["topic"],
        max_turns=session["max_turns"],
        proposer_model=session["proposer_model"],
        opponent_model=session["opponent_model"],
        fact_model=session["fact_model"],
        resolution=session["frame"].resolution,
        proposer_position=session["frame"].proposer_position,
        opponent_position=session["frame"].opponent_position,
        fact_base=session["fact_texts"],
        turns=session["turns"],
        status=session["status"],
        summary=session.get("summary"),
    )


@router.get("/mcts-trace/{debate_id}/{turn_number}", response_model=MCTSTrace)
def get_mcts_trace(debate_id: str, turn_number: int) -> MCTSTrace:
    """Retrieve MCTS reasoning trace for a specific turn."""
    session = _get_session(debate_id)
    for turn in session["turns"]:
        if turn.turn_number == turn_number:
            if turn.mcts_trace:
                return turn.mcts_trace
            raise HTTPException(status_code=404, detail=f"MCTS was not invoked on turn {turn_number}")
    raise HTTPException(status_code=404, detail=f"Turn {turn_number} not found in debate '{debate_id}'")


@router.get("/summary/{debate_id}", response_model=DebateSummary)
def get_debate_summary(debate_id: str) -> DebateSummary:
    """Retrieve the debate summary and verdict, building it on first request."""
    session = _get_session(debate_id)
    session["status"] = "complete"
    if not session.get("summary"):
        _synthesize_debate_summary(session)
    return session["summary"]
