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
from agents.nvidia_agent import NvidiaAgent, is_groq_model, is_openrouter_model
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_MODEL_FALLBACKS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL_FALLBACKS,
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL_FALLBACKS,
    MCTS_N_SIMULATIONS,
    FACT_BASE_SIZE,
)
from core.fact_generation import (
    FactRecord,
    extract_fact_texts,
    extract_valid_clauses,
    generate_fact_base,
    generate_fact_base_openai,
)
from core.topic_knowledge import get_topic_grounded_facts, get_targeted_rebuttal, clean_claim_text
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

                                                                                               
    clear_index()

    proposer_model = req.proposer_model or "openai/gpt-oss-120b"
    opponent_model = req.opponent_model or "deepseek/deepseek-r1-distill-llama-70b"

    facts: list[FactRecord] = []

    # Dedicated ultra-fast model responsible for fetching the 20 grounded facts & propositional clauses:
    CLAUSE_FETCHING_MODEL = "openai/gpt-oss-120b"

    if GROQ_API_KEY:
        try:
            facts = generate_fact_base_openai(topic, GROQ_API_KEY, GROQ_BASE_URL, CLAUSE_FETCHING_MODEL, n_facts=FACT_BASE_SIZE)
        except Exception as e:
            logger.warning(f"Groq LPU clause generation failed ({e}). Trying fallback...")

    if not facts and GEMINI_API_KEY:
        for model_name in GEMINI_MODEL_FALLBACKS:
            try:
                facts = generate_fact_base(topic, GEMINI_API_KEY, n_facts=FACT_BASE_SIZE, model_name=model_name)
                if facts:
                    break
            except Exception as e:
                logger.warning(f"Gemini fact generation fallback failed with '{model_name}' ({e}). Trying next model...")
                continue

    if not facts and OPENROUTER_API_KEY:
        try:
            facts = generate_fact_base_openai(topic, OPENROUTER_API_KEY, OPENROUTER_BASE_URL, "meta-llama/llama-3.3-70b-instruct", n_facts=FACT_BASE_SIZE)
        except Exception as e:
            logger.warning(f"OpenRouter fact generation fallback failed ({e})...")

    if not facts:
        facts = _generate_fallback_facts(topic)

    fact_texts = extract_fact_texts(facts)
    valid_clauses = extract_valid_clauses(facts)

    # Fast, deterministic semantic fact retrieval index (instant sub-millisecond execution, zero network stalls)
    embed_fn = _fallback_embed_fn
    fact_index = build_index(fact_texts, embed_fn)

                                                         
    def _create_agent(agent_id: str, role: str, model_name: str):
        if "/" in model_name or "llama" in model_name.lower() or "deepseek" in model_name.lower() or "nemotron" in model_name.lower():
            return NvidiaAgent(agent_id=agent_id, role=role, model_name=model_name)
        return GeminiAgent(agent_id=agent_id, role=role)

                                                 
    proposer_model = req.proposer_model or "openai/gpt-oss-120b"
    opponent_model = req.opponent_model or "deepseek/deepseek-r1-distill-llama-70b"

    agent_a = _create_agent("agent_a", "proposer", proposer_model)
    agent_b = _create_agent("agent_b", "opponent", opponent_model)

                                               
    for clause in valid_clauses[:len(valid_clauses) // 2]:
        agent_a.kb.tell(clause)
    for clause in valid_clauses[len(valid_clauses) // 2:]:
        agent_b.kb.tell(clause)

    max_turns = req.max_turns if req.max_turns and req.max_turns > 0 else 20

                                                                                
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

                       
    is_agent_a = (turn_number % 2 != 0)
    current_agent = session["agent_a"] if is_agent_a else session["agent_b"]
    other_agent = session["agent_b"] if is_agent_a else session["agent_a"]

    opponent_last_claim = turns[-1].claim.text if turns else None

                                 
    ctx = ExecutorContext(
        agent_kb=current_agent.kb,
        opponent_kb=other_agent.kb,
        embed_fn=session["embed_fn"],
        fact_index=session["fact_index"],
        debate_state=session["debate_state"],
        n_simulations=MCTS_N_SIMULATIONS,
        agent_id=current_agent.agent_id,
    )

                    
    res = current_agent.run_turn(
        topic=session["topic"],
        opponent_last_claim=opponent_last_claim,
        turn_number=turn_number,
        ctx=ctx,
    )

                                        
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

    agent_model = session.get("proposer_model", "Groq Llama 3.3 70B") if is_agent_a else session.get("opponent_model", "Groq Llama 3.3 70B")
    speaker_name = f"Agent {'A' if is_agent_a else 'B'} ({agent_model})"
    print(f"\n--------------------------------------------------", flush=True)
    print(f" 📢 TURN #{turn_number}/{max_turns} | SPEAKER: {speaker_name}", flush=True)
    print(f" 🗣️  Claim: {claim_obj.text}", flush=True)
    print(f" 📐 Clause: {claim_obj.propositional_form}", flush=True)
    print(f" ⚡ Contradiction Found: {contradiction_result.found}", flush=True)
    if mcts_trace:
        print(f" 🌳 MCTS Chosen Rebuttal: {mcts_trace.chosen_rebuttal}", flush=True)
    print(f"--------------------------------------------------\n", flush=True)

    # 5. Check if debate limit reached
    if turn_number >= max_turns:
        session["status"] = "complete"
        print(f"\n🏁 DEBATE REACHED MAX TURNS ({turn_number}/{max_turns}) for topic: '{session['topic']}'\n", flush=True)

    return turn_obj


def _generate_live_counter_reply(topic: str, attack_claim: str, defending_role: str, model_hint: str = None) -> str:
    """
    Generate a concrete, specific counter-argument for a given attack claim using ultra-fast Groq/NVIDIA endpoints.
    Falls back to Gemini if needed.
    """
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

    if OPENROUTER_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
            fast_model = model_hint if (model_hint and is_openrouter_model(model_hint) and "deepseek" not in model_hint.lower()) else "meta-llama/llama-3.3-70b-instruct"
            res = client.chat.completions.create(
                model=fast_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                timeout=7.0,
            )
            msg = res.choices[0].message
            text = (msg.content or "").strip()
            if "</think>" in text:
                text = text.split("</think>")[-1].strip()
            if text:
                return clean_claim_text(text)
        except Exception as e:
            logger.warning(f"OpenRouter counter reply failed ({e}).")

    if GROQ_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)
            model_name = GROQ_MODEL_FALLBACKS[0]
            if model_hint and is_groq_model(model_hint):
                model_name = model_hint
            res = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                timeout=6.0,
            )
            text = (res.choices[0].message.content or "").strip()
            if text:
                return clean_claim_text(text)
        except Exception as e:
            logger.warning(f"Groq counter reply failed ({e}).")

    if NVIDIA_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)
            model_name = "nvidia/llama-3.3-nemotron-super-49b-v1"
            if model_hint and ("/" in model_hint or "llama" in model_hint):
                model_name = model_hint
            res = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                timeout=6.0,
            )
            text = (res.choices[0].message.content or "").strip()
            if text:
                return clean_claim_text(text)
        except Exception as e:
            logger.warning(f"NVIDIA counter reply failed ({e}).")

    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            for m in GEMINI_MODEL_FALLBACKS:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=prompt,
                    )
                    text = (response.text or "").strip()
                    if text:
                        return clean_claim_text(text)
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Gemini counter reply failed ({e}).")

    return None


def _parse_summary_json(text: str) -> dict[str, Any]:
    """Parse JSON output from LLM summary debrief."""
    try:
        clean = text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        if clean.startswith("json"):
            clean = clean[4:].strip()
        return json.loads(clean)
    except Exception:
        return {}


def _generate_proposer_summary_debrief(
    topic: str,
    turns: list[Turn],
    proposer_model: str,
    winner: str,
    score_a: float,
) -> dict[str, Any]:
    """
    Call the Proposer Agent's LLM to generate an intense post-debate strategic cornering debrief.
    Analyzes:
    1. Where Proposer can be cornered + Proposer's counter-defense.
    2. Where Opponent can be cornered.
    3. How Opponent can escape if cornered in that trap.
    """
    recent_history = "\n".join([f"Turn #{t.turn_number} ({'Proposer' if t.claim.speaker == 'agent_a' else 'Opponent'}): {t.claim.text}" for t in turns[-8:]])

    prompt = (
        f"You are Agent A (Proposer), writing the official Post-Debate Strategic Debrief for topic: '{topic}'.\n\n"
        f"Debate Exchanges:\n{recent_history}\n\n"
        f"Debate Winner: {winner}.\n\n"
        f"Perform an intense strategic analysis from the Proposer's perspective.\n"
        f"CRITICAL DIRECTIVE ON SPECIFICITY:\n"
        f"- Every field MUST contain the EXACT, CONCRETE debate argument or counter-claim to be spoken aloud.\n"
        f"- DO NOT write vague meta-instructions like 'pivot to resource constraints', 'emphasize ROI', or 'focus on trade-offs'.\n"
        f"- Instead, write the exact substantive sentence with facts and logical reasons that the debater must say.\n\n"
        f"Output JSON format strictly as:\n"
        f"{{\n"
        f'  "verdict_statement": "2-sentence executive summary explaining why {winner} won on \'{topic}\'",\n'
        f'  "proposer_cornered_analysis": "Specifically quote the toughest attack against Agent A (Proposer) and provide the EXACT substantive counter-claim Agent A must say to refute it",\n'
        f'  "opponent_cornered_analysis": "Specifically state the exact premise that traps and corners Agent B (Opponent)",\n'
        f'  "opponent_escape_route": "The EXACT substantive verbal rebuttal claim and evidence Agent B (Opponent) must say aloud to escape that trap",\n'
        f'  "key_proposer_points": ["Specific Proposer Argument 1", "Specific Proposer Argument 2"],\n'
        f'  "key_opponent_points": ["Specific Opponent Argument 1", "Specific Opponent Argument 2"]\n'
        f"}}\n"
    )

    if OPENROUTER_API_KEY and is_openrouter_model(proposer_model):
        try:
            from openai import OpenAI
            client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
            res = client.chat.completions.create(
                model=proposer_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                timeout=18.0,
            )
            msg = res.choices[0].message
            raw = (msg.content or (msg.reasoning if hasattr(msg, "reasoning") else "") or "").strip()
            if "</think>" in raw:
                raw = raw.split("</think>")[-1].strip()
            parsed = _parse_summary_json(raw)
            if parsed and "proposer_cornered_analysis" in parsed:
                return parsed
        except Exception as e:
            logger.warning(f"OpenRouter summary debrief failed ({e}).")

    if is_groq_model(proposer_model) and GROQ_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)
            res = client.chat.completions.create(
                model=proposer_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                timeout=12.0,
            )
            raw = res.choices[0].message.content or ""
            parsed = _parse_summary_json(raw)
            if parsed and "proposer_cornered_analysis" in parsed:
                return parsed
        except Exception as e:
            logger.warning(f"Groq summary debrief failed ({e}).")

    if not is_groq_model(proposer_model) and ("/" in proposer_model or "nemotron" in proposer_model.lower()) and NVIDIA_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)
            res = client.chat.completions.create(
                model=proposer_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                timeout=12.0,
            )
            raw = res.choices[0].message.content or ""
            parsed = _parse_summary_json(raw)
            if parsed and "proposer_cornered_analysis" in parsed:
                return parsed
        except Exception as e:
            logger.warning(f"NVIDIA summary debrief failed ({e}).")

    if GROQ_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)
            res = client.chat.completions.create(
                model=GROQ_MODEL_FALLBACKS[0],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                timeout=10.0,
            )
            raw = res.choices[0].message.content or ""
            parsed = _parse_summary_json(raw)
            if parsed and "proposer_cornered_analysis" in parsed:
                return parsed
        except Exception as e:
            logger.warning(f"Groq fallback summary debrief failed ({e}).")

    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            res = client.models.generate_content(
                model=GEMINI_MODEL_FALLBACKS[0],
                contents=prompt,
            )
            raw = (res.text or "").strip()
            parsed = _parse_summary_json(raw)
            if parsed and "proposer_cornered_analysis" in parsed:
                return parsed
        except Exception as e:
            logger.warning(f"Gemini summary debrief failed ({e}).")

    return {}


def _synthesize_debate_summary(session: dict[str, Any]) -> DebateSummary:
    """Generate structured DebateSummary object of completed debate session authored by Proposer Agent."""
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

    proposer_model = session.get("proposer_model", "gemini-3.6-flash")

    debrief = _generate_proposer_summary_debrief(
        topic=topic,
        turns=turns,
        proposer_model=proposer_model,
        winner=winner,
        score_a=score_a,
    )

    # Prepare concrete fallbacks derived from actual spoken claims or domain points
    sample_opp_att = opp_claims[0] if opp_claims else f"Implementation overhead and practical constraints make {topic} unviable."
    sample_pro_reb = get_targeted_rebuttal(topic, sample_opp_att, "proposer") or (pro_claims[0] if pro_claims else f"Standardized adoption of {topic} yields measurable operational efficiency and long-term utility.")
    sample_pro_att = pro_claims[0] if pro_claims else f"Adopting {topic} provides structured advantages that outweigh incidental downsides."
    sample_opp_reb = get_targeted_rebuttal(topic, sample_pro_att, "opponent") or (opp_claims[0] if opp_claims else f"Alternative lightweight options deliver the same benefits without the mandatory costs of {topic}.")

    p_cornered = debrief.get(
        "proposer_cornered_analysis",
        f"Agent A (Proposer) faces risk when Opponent asserts: \"{sample_opp_att}\". Proposer's verbal defense: \"{sample_pro_reb}\""
    )
    o_cornered = debrief.get(
        "opponent_cornered_analysis",
        f"Agent B (Opponent) gets cornered when Proposer establishes: \"{sample_pro_att}\""
    )
    o_escape = debrief.get(
        "opponent_escape_route",
        f"Opponent escapes this corner by arguing: \"{sample_opp_reb}\""
    )

    cornering_points = []
    best_opp_attack = max(opp_claims, key=len) if opp_claims else None
    best_pro_attack = max(pro_claims, key=len) if pro_claims else None

    if best_opp_attack:
        reb_b = (
            _generate_live_counter_reply(topic, best_opp_attack, "proposer", proposer_model)
            or get_targeted_rebuttal(topic, best_opp_attack, "proposer")
            or f"Empirical data demonstrates that {topic} establishes a dependable operational framework that mitigates this concern."
        )
        opp_followup_escape = (
            _generate_live_counter_reply(topic, reb_b, "opponent", session.get("opponent_model"))
            or get_targeted_rebuttal(topic, reb_b, "opponent")
            or f"Opponent can counter-argue: \"Field studies show real-world compliance issues frequently negate these theoretical gains.\""
        )
        cornering_points.append(
            CorneringPoint(
                point=best_opp_attack,
                speaker="Agent B (Opponent)",
                risk_level="HIGH THREAT",
                why_dangerous=f"Directly challenges the core practical feasibility of the proposer's argument on '{topic}'.",
                best_reply=reb_b,
                escape_route=opp_followup_escape,
            )
        )

    if best_pro_attack:
        reb_a = (
            _generate_live_counter_reply(topic, best_pro_attack, "opponent", session.get("opponent_model"))
            or get_targeted_rebuttal(topic, best_pro_attack, "opponent")
            or f"This claim assumes ideal conditions that fail to hold in dynamic environments, undermining the proposer's premise."
        )
        cornering_points.append(
            CorneringPoint(
                point=best_pro_attack,
                speaker="Agent A (Proposer)",
                risk_level="TACTICAL CORNER",
                why_dangerous=f"Establishes a strong proactive standard that puts the opponent on the defensive.",
                best_reply=reb_a,
                escape_route=o_escape,
            )
        )

    if not cornering_points:
        cornering_points = [
            CorneringPoint(
                point=sample_opp_att,
                speaker="Agent B (Opponent)",
                risk_level="HIGH THREAT",
                why_dangerous="Exposes potential vulnerability if premises lack direct empirical verification.",
                best_reply=sample_pro_reb,
                escape_route=o_escape,
            )
        ]

    verdict_stmt = debrief.get("verdict_statement") or f"Debate on '{topic}' concluded after {total_turns} turns. Winner: {winner}."
    pro_pts = debrief.get("key_proposer_points") or pro_claims[:3]
    opp_pts = debrief.get("key_opponent_points") or opp_claims[:3]

    summary_obj = DebateSummary(
        debate_id=session["debate_id"],
        topic=topic,
        total_turns=total_turns,
        winner=winner,
        winner_reasoning=reasoning,
        proposer_key_points=pro_pts,
        opponent_key_points=opp_pts,
        total_contradictions=contradictions,
        verdict_statement=verdict_stmt,
        proposer_cornered_analysis=p_cornered,
        opponent_cornered_analysis=o_cornered,
        opponent_escape_route=o_escape,
        cornering_points=cornering_points,
        proposer_full_arguments=pro_claims,
        opponent_full_arguments=opp_claims,
    )
    session["summary"] = summary_obj
    return summary_obj


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
    session["status"] = "complete"
    if not session.get("summary"):
        try:
            session["summary"] = _synthesize_debate_summary(session)
        except Exception as e:
            logger.error(f"Failed to synthesize debate summary ({e}). Using resilient fallback.", exc_info=True)
            topic = session["topic"]
            turns = session.get("turns", [])
            pro_claims = [t.claim.text for t in turns if t.claim.speaker == "agent_a"]
            opp_claims = [t.claim.text for t in turns if t.claim.speaker == "agent_b"]
            winner = "Agent A (Proposer)" if len(pro_claims) >= len(opp_claims) else "Agent B (Opponent)"
            session["summary"] = DebateSummary(
                debate_id=debate_id,
                topic=topic,
                total_turns=len(turns),
                winner=winner,
                winner_reasoning=f"Debate concluded after {len(turns)} turns. {winner} established strong grounded premises.",
                proposer_key_points=pro_claims[:3] or [f"Proposer advocated for {topic}."],
                opponent_key_points=opp_claims[:3] or [f"Opponent challenged core trade-offs of {topic}."],
                total_contradictions=0,
                verdict_statement=f"Debate on '{topic}' concluded across {len(turns)} rounds.",
                proposer_cornered_analysis=f"Proposer relied on structured claims on '{topic}'.",
                opponent_cornered_analysis=f"Opponent counter-argued against potential constraints.",
                opponent_escape_route="Opponent can pivot to implementation challenges.",
                cornering_points=[],
                proposer_full_arguments=pro_claims,
                opponent_full_arguments=opp_claims,
            )
    return session["summary"]
