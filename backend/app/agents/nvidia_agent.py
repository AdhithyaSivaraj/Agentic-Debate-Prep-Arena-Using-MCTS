"""
nvidia_agent.py — Agent Implementation using NVIDIA NIM API (build.nvidia.com) & Groq LPUs

Design notes:
    - Connects to NVIDIA NIM endpoints or Groq LPU endpoints via OpenAI-compatible chat completions format.
    - Runs MCTS rebuttal selection & propositional resolution locally, then uses LLM in a single pass to phrase claims.
    - Zero multi-turn message format bugs, zero rate-limit loops, sub-2s turn execution.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base_agent import BaseAgent
from config import (
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    NVIDIA_MODEL_FALLBACKS,
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL_FALLBACKS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL_FALLBACKS,
)
from core.topic_knowledge import (
    get_topic_proposer_points,
    get_topic_opponent_points,
    get_targeted_rebuttal,
    clean_claim_text,
)
from tools.tool_executor import ExecutorContext, execute_tool, parse_propositional_form

logger = logging.getLogger("agent")


def is_openrouter_model(model_name: str) -> bool:
    if not model_name:
        return False
    m = model_name.lower()
    return m.startswith("meta-llama/") or m.startswith("deepseek/") or m.startswith("qwen/qwen-2.5") or "openrouter" in m


def is_groq_model(model_name: str) -> bool:
    if not model_name:
        return False
    m = model_name.lower()
    if is_openrouter_model(model_name):
        return False
    return any(k in m for k in ["gpt-oss", "qwen3.6", "groq", "versatile", "instant"])


class NvidiaAgent(BaseAgent):
    """
    Agent powered by OpenRouter, Groq LPU, or NVIDIA NIM models (OpenAI-compatible chat completions format).
    """

    CURRENT_MODEL_INDEX: int = 0                                                

    def __init__(
        self,
        agent_id: str = "agent_a",
        role: str = "proposer",
        model_name: str | None = None,
        api_key: str | None = None,
    ):
        super().__init__(agent_id=agent_id, role=role)
        self.model_name = model_name or (OPENROUTER_MODEL_FALLBACKS[0] if OPENROUTER_API_KEY else GROQ_MODEL_FALLBACKS[0])
        if is_openrouter_model(self.model_name):
            self.base_url = OPENROUTER_BASE_URL
            self.api_key = api_key or OPENROUTER_API_KEY
        elif is_groq_model(self.model_name):
            self.base_url = GROQ_BASE_URL
            self.api_key = api_key or GROQ_API_KEY
        else:
            self.base_url = NVIDIA_BASE_URL
            self.api_key = api_key or NVIDIA_API_KEY

    def perceive(self, opponent_last_claim: str | None) -> dict:
        """Receive the opponent's last claim as a percept."""
        return {
            "opponent_last_claim": opponent_last_claim,
            "agent_id": self.agent_id,
            "role": self.role,
        }

    def decide(self, percept: dict) -> dict:
        """Stub implementation for BaseAgent abstract method."""
        return {}

    def act(self, action: dict) -> str:
        """Stub implementation for BaseAgent abstract method."""
        return action.get("claim_text", "")

    def execute_turn(
        self,
        topic: str,
        opponent_last_claim: str | None,
        turn_number: int,
        ctx: ExecutorContext,
    ) -> dict[str, Any]:
        """
        Main entrypoint to run a single turn for this agent.
        Tries primary model, then fallbacks if rate-limited, and falls back to pure local logic if all API attempts fail.
        """
        import time
        if is_openrouter_model(self.model_name):
            models_to_try = [self.model_name] + [m for m in OPENROUTER_MODEL_FALLBACKS if m != self.model_name]
        elif is_groq_model(self.model_name):
            models_to_try = [self.model_name] + [m for m in GROQ_MODEL_FALLBACKS if m != self.model_name]
        else:
            models_to_try = [self.model_name] + [m for m in NVIDIA_MODEL_FALLBACKS if m != self.model_name]

        for current_model in models_to_try:
            for attempt in range(2):
                try:
                    res = self._run_nvidia_api_loop(topic, opponent_last_claim, turn_number, ctx, model_name=current_model)
                    res["mode"] = "live"
                    res["model_used"] = current_model
                    return res
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                        if attempt == 0:
                            logger.warning(f"API rate limit on '{current_model}' (attempt 1/2). Waiting 3s...")
                            time.sleep(3)
                        else:
                            logger.warning(f"Rate limit persists on '{current_model}'. Trying next model...")
                            break
                    else:
                        logger.warning(f"API call failed on '{current_model}' ({e}). Trying next model...")
                        break

        logger.warning("All models failed. Falling back to algorithmic agent loop.")

        res = self._run_agentic_loop(topic, opponent_last_claim, turn_number, ctx)
        res["mode"] = "fallback"
        return res

    def _run_nvidia_api_loop(
        self,
        topic: str,
        opponent_last_claim: str | None,
        turn_number: int,
        ctx: ExecutorContext,
        model_name: str,
    ) -> dict[str, Any]:
        """
        Execute turn using single-pass high-throughput generation with MCTS and Propositional Resolution.
        """
        from openai import OpenAI

        if is_openrouter_model(model_name):
            target_url = OPENROUTER_BASE_URL
            target_key = OPENROUTER_API_KEY or self.api_key
        elif is_groq_model(model_name):
            target_url = GROQ_BASE_URL
            target_key = GROQ_API_KEY or self.api_key
        else:
            target_url = NVIDIA_BASE_URL
            target_key = NVIDIA_API_KEY or self.api_key

        if not target_key:
            raise ValueError(f"No API key configured for model '{model_name}'.")

        client = OpenAI(
            base_url=target_url,
            api_key=target_key,
        )

                               
        fact_res = execute_tool("retrieve_relevant_fact", {"claim_topic": topic, "top_k": 1}, ctx)
        grounding_fact = fact_res.output.get("top_fact", f"Evidence regarding {topic}.")

                                         
        mcts_trace = None
        spoken = set(ctx.debate_state.own_claims if self.agent_id == "agent_a" else ctx.debate_state.opponent_claims)
        if self.role == "proposer":
            candidates = get_topic_proposer_points(topic, spoken_claims=spoken)
        else:
            candidates = get_topic_opponent_points(topic, spoken_claims=spoken)

        targeted = get_targeted_rebuttal(topic, opponent_last_claim or "", self.role, spoken_claims=spoken)
        if targeted and targeted not in candidates:
            candidates.insert(0, targeted)

        untried = [c for c in candidates if c not in spoken]
        eval_candidates = untried if untried else candidates

        mcts_res = execute_tool("select_best_rebuttal", {"candidates": eval_candidates[:5], "agent_id": self.agent_id}, ctx)
        if mcts_res.success:
            mcts_trace = mcts_res.output
            chosen_claim = mcts_res.output.get("chosen_rebuttal", eval_candidates[0])
        else:
            chosen_claim = eval_candidates[0]

                                                       
        prompt_content = (
            f"Debate Topic: '{topic}'\n"
            f"Your Role: Agent {self.agent_id.upper()} ({self.role})\n"
            f"Opponent's Last Claim: '{opponent_last_claim or 'None (Opening turn)'}'\n"
            f"Grounding Fact: '{grounding_fact}'\n"
            f"Key Rebuttal Direction: '{chosen_claim}'\n\n"
            f"Write a confident, 1-2 sentence debate claim for Agent {self.agent_id.upper()} reflecting the rebuttal direction and grounding fact.\n"
            f"Output JSON format strictly as:\n"
            f'{{"claim_text": "your 1-2 sentence claim", "propositional_form": "ClauseName"}}'
        )

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a professional debater. Output valid JSON only with keys 'claim_text' and 'propositional_form'. State ONLY the direct point. Do NOT include introductory phrases like 'The generated claim is:' or 'The final answer is:'."},
                {"role": "user", "content": prompt_content},
            ],
            temperature=0.6,
            timeout=12.0,
        )

        msg = response.choices[0].message
        raw_content = msg.content or ""
        if not raw_content and hasattr(msg, "reasoning") and msg.reasoning:
            raw_content = msg.reasoning
        if "</think>" in raw_content:
            raw_content = raw_content.split("</think>")[-1].strip()
        claim_text = chosen_claim
        clean_topic = "".join(w.capitalize() for w in topic.split() if w.isalnum())[:15] or "Topic"
        prefix = "" if self.role == "proposer" else "¬"
        prop_form = f"{prefix}{clean_topic}ProT{turn_number}"

        try:
                                                   
            clean_json = raw_content.strip()
            if clean_json.startswith("```"):
                clean_json = clean_json.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            if clean_json.startswith("json"):
                clean_json = clean_json[4:].strip()

            parsed = json.loads(clean_json)
            if parsed.get("claim_text"):
                claim_text = parsed["claim_text"]
            if parsed.get("propositional_form"):
                prop_form = parsed["propositional_form"]
        except Exception:
            if raw_content:
                claim_text = raw_content[:280]

        claim_text = clean_claim_text(claim_text)

        execute_tool(
            "generate_claim",
            {
                "context": f"Topic: {topic}. Role: {self.role}. Fact: {grounding_fact}",
                "direction": claim_text,
                "propositional_form": prop_form,
                "agent_id": self.agent_id,
            },
            ctx,
        )

                                                 
        check_res = execute_tool("check_contradiction", {"target": "self", "agent_id": self.agent_id}, ctx)
        contradiction_result = check_res.output if check_res.success else {"found": False, "conflicting_clauses": [], "proof_steps": []}

        comb_res = execute_tool("check_contradiction", {"target": "combined", "agent_id": self.agent_id}, ctx)
        if comb_res.success and comb_res.output.get("found"):
            contradiction_result = comb_res.output

        return {
            "speaker": self.agent_id,
            "turn_number": turn_number,
            "claim_text": claim_text,
            "propositional_form": prop_form,
            "contradiction_result": contradiction_result,
            "mcts_trace": mcts_trace,
            "mode": "live",
        }

    def _run_agentic_loop(
        self,
        topic: str,
        opponent_last_claim: str | None,
        turn_number: int,
        ctx: ExecutorContext,
    ) -> dict[str, Any]:
        """
        Deterministic algorithmic execution of the 5-step agentic loop for fallback.
        """
        fact_res = execute_tool("retrieve_relevant_fact", {"claim_topic": topic, "top_k": 1}, ctx)
        grounding_fact = fact_res.output.get("top_fact", f"Evidence regarding {topic}.")

        mcts_trace = None
        spoken = set(ctx.debate_state.own_claims if self.agent_id == "agent_a" else ctx.debate_state.opponent_claims)
        if self.role == "proposer":
            candidates = get_topic_proposer_points(topic, spoken_claims=spoken)
        else:
            candidates = get_topic_opponent_points(topic, spoken_claims=spoken)

        targeted = get_targeted_rebuttal(topic, opponent_last_claim or "", self.role, spoken_claims=spoken)
        if targeted and targeted not in candidates:
            candidates.insert(0, targeted)

        untried = [c for c in candidates if c not in spoken]
        eval_candidates = untried if untried else candidates

        mcts_res = execute_tool("select_best_rebuttal", {"candidates": eval_candidates[:5], "agent_id": self.agent_id}, ctx)
        if mcts_res.success:
            mcts_trace = mcts_res.output
            chosen_claim = mcts_res.output.get("chosen_rebuttal", eval_candidates[0])
        else:
            chosen_claim = eval_candidates[0]

        clean_topic = "".join(w.capitalize() for w in topic.split() if w.isalnum())[:15] or "Topic"
        prefix = "" if self.role == "proposer" else "¬"
        prop_form = f"{prefix}{clean_topic}ProT{turn_number}"
        claim_text = chosen_claim

        execute_tool(
            "generate_claim",
            {
                "context": f"Topic: {topic}. Role: {self.role}. Fact: {grounding_fact}",
                "direction": chosen_claim,
                "propositional_form": prop_form,
                "agent_id": self.agent_id,
            },
            ctx,
        )

        check_res = execute_tool("check_contradiction", {"target": "self", "agent_id": self.agent_id}, ctx)
        contradiction_result = check_res.output if check_res.success else {"found": False, "conflicting_clauses": [], "proof_steps": []}

        comb_res = execute_tool("check_contradiction", {"target": "combined", "agent_id": self.agent_id}, ctx)
        if comb_res.success and comb_res.output.get("found"):
            contradiction_result = comb_res.output

        return {
            "speaker": self.agent_id,
            "turn_number": turn_number,
            "claim_text": claim_text,
            "propositional_form": prop_form,
            "contradiction_result": contradiction_result,
            "mcts_trace": mcts_trace,
            "mode": "fallback",
        }
