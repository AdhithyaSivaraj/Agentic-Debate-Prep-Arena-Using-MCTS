"""
nemotron_agent.py — Agent B Implementation Using Nemotron 3 Ultra (via OpenRouter)

Design notes:
    - Uses Nemotron 3 Ultra via OpenRouter (OpenAI-compatible chat completion format).
    - Wired to the EXACT SAME tool schemas as gemini_agent.py (defined in tool_schemas.py via as_openai_tools).
    - The LLM is used ONLY for phrasing claims and deciding tool call order.
    - Includes deterministic fallback execution when OpenRouter API keys are not set or network is offline.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from agents.base_agent import BaseAgent
from config import NEMOTRON_CHAT_MODEL, OPENROUTER_API_KEY
from core.topic_knowledge import get_topic_opponent_points, get_targeted_rebuttal
from tools.tool_executor import ExecutorContext, execute_tool
from tools.tool_schemas import as_openai_tools

logger = logging.getLogger(__name__)


class NemotronAgent(BaseAgent):
    """
    Agent B: brain = Nemotron 3 Ultra via OpenRouter with function calling.
    Role: Opponent (by default).
    """

    def __init__(self, agent_id: str = "agent_b", role: str = "opponent", api_key: str | None = None):
        super().__init__(agent_id=agent_id, role=role)
        self.api_key = api_key or OPENROUTER_API_KEY

    def perceive(self, opponent_last_claim: str | None) -> dict:
        """Receive the opponent's last claim as a percept."""
        return {
            "opponent_last_claim": opponent_last_claim,
            "agent_id": self.agent_id,
            "role": self.role,
        }

    def decide(self, percept: dict) -> dict:
        """Stub implementation for BaseAgent abstract method."""
        return percept

    def act(self, action: dict) -> str:
        """Stub implementation for BaseAgent abstract method."""
        return action.get("claim_text", "")

    def run_turn(
        self,
        topic: str,
        opponent_last_claim: str | None,
        turn_number: int,
        ctx: ExecutorContext,
    ) -> dict[str, Any]:
        """
        Run the autonomous agentic loop for Agent B (Nemotron) for one debate turn.
        """
        ctx.agent_id = self.agent_id

                                                         
        if self.api_key:
            try:
                res = self._run_openrouter_api_loop(topic, opponent_last_claim, turn_number, ctx)
                res["mode"] = "live"
                return res
            except Exception as e:
                logger.warning(f"Nemotron OpenRouter API call failed ({e}). Falling back to algorithmic agent loop.")

                                                       
        res = self._run_agentic_loop(topic, opponent_last_claim, turn_number, ctx)
        res["mode"] = "fallback"
        return res

    def _run_openrouter_api_loop(
        self,
        topic: str,
        opponent_last_claim: str | None,
        turn_number: int,
        ctx: ExecutorContext,
    ) -> dict[str, Any]:
        """Execute turn using OpenAI SDK pointing to OpenRouter API."""
        from openai import OpenAI

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

        tools = as_openai_tools()
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    f"You are Agent B ({self.role}) debating on topic: '{topic}'. "
                    "Call tools to structure your argument: "
                    "`retrieve_relevant_fact`, `select_best_rebuttal` if responding to attack, "
                    "`generate_claim` with context/direction/propositional_form, and `check_contradiction`."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Turn {turn_number}. Topic: '{topic}'. "
                    f"Opponent last claim: '{opponent_last_claim or 'None (Opening turn)'}'."
                ),
            },
        ]

        mcts_trace = None
        contradiction_result = {"found": False, "conflicting_clauses": [], "proof_steps": []}
        generated_claim = None
        claim_text = ""

                                                      
        for _ in range(8):
            response = client.chat.completions.create(
                model=NEMOTRON_CHAT_MODEL,
                messages=messages,
                tools=tools,
                temperature=0.7,
            )

            choice = response.choices[0]
            msg = choice.message

            if not msg.tool_calls:
                claim_text = msg.content or ""
                break

                                                      
            messages.append(msg.model_dump())

                                    
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                try:
                    fn_args = json.loads(tool_call.function.arguments)
                except Exception:
                    fn_args = {}

                tool_res = execute_tool(fn_name, fn_args, ctx)

                                
                if fn_name == "select_best_rebuttal" and tool_res.success:
                    mcts_trace = tool_res.output
                elif fn_name == "check_contradiction" and tool_res.success:
                    contradiction_result = tool_res.output
                elif fn_name == "generate_claim" and tool_res.success:
                    generated_claim = tool_res.output

                                      
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": tool_res.to_llm_message(),
                })

        if not generated_claim:
            res = self._run_agentic_loop(topic, opponent_last_claim, turn_number, ctx)
            res["mode"] = "fallback"
            return res

        if not claim_text:
            claim_text = generated_claim.get("direction", f"Opposing argument on {topic}")

        prop_form = generated_claim.get("propositional_form", "OpponentClaim")

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
        Deterministic algorithmic execution of the 5-step agentic loop.
        Replaces ONLY language generation — resolution and MCTS execute for real.
        """
                               
        fact_res = execute_tool("retrieve_relevant_fact", {"claim_topic": topic, "top_k": 1}, ctx)
        grounding_fact = fact_res.output.get("top_fact", f"Counter-evidence regarding {topic}.")

                                                                                         
        mcts_trace = None
        spoken = set(ctx.debate_state.opponent_claims)
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
        prop_form = f"¬{clean_topic}ProT{turn_number}"
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
