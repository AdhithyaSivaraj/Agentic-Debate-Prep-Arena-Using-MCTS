"""
gemini_agent.py — Agent A Implementation Using Gemini Function Calling

Design notes:
    - Uses Google Gemini API (native function/tool calling).
    - Wired to the SAME tool schemas as nemotron_agent.py (defined in tool_schemas.py).
    - The LLM is used ONLY for: (a) phrasing claims in fluent language, (b) deciding which
      tool to call next. It NEVER decides contradictions or best rebuttals — those are
      delegated to resolution.py and mcts.py respectively.
    - Includes robust fallback execution when API keys are not set or network is unavailable,
      ensuring system stability in offline / test environments.
"""
from __future__ import annotations

import logging
from typing import Any

from agents.base_agent import BaseAgent
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MODEL_FALLBACKS
from core.topic_knowledge import (
    get_topic_proposer_points,
    get_topic_opponent_points,
    get_targeted_rebuttal,
    clean_claim_text,
)
from tools.tool_executor import ExecutorContext, execute_tool
from tools.tool_schemas import TOOL_SCHEMAS

logger = logging.getLogger(__name__)


def _prepare_gemini_tools(schemas: list[dict]) -> list[dict]:
    """Convert JSON schema type strings to UPPERCASE for google.generativeai SDK compatibility."""
    import copy
    result = copy.deepcopy(schemas)
    def _to_upper(obj):
        if isinstance(obj, dict):
            if "type" in obj and isinstance(obj["type"], str):
                obj["type"] = obj["type"].upper()
            for v in obj.values():
                _to_upper(v)
        elif isinstance(obj, list):
            for item in obj:
                _to_upper(item)
    _to_upper(result)
    return result


class GeminiAgent(BaseAgent):
    """
    Agent A: brain = Gemini API with function calling.
    Role: Proposer (by default).
    """

    CURRENT_MODEL_INDEX: int = 0                                                

    def __init__(self, agent_id: str = "agent_a", role: str = "proposer", api_key: str | None = None):
        super().__init__(agent_id=agent_id, role=role)
        self.api_key = api_key or GEMINI_API_KEY

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
        Run the autonomous agentic loop for Agent A (Gemini) for one debate turn.
        """
        ctx.agent_id = self.agent_id

                                                                                                      
        if self.api_key:
            import time
            num_models = len(GEMINI_MODEL_FALLBACKS)
            start_idx = GeminiAgent.CURRENT_MODEL_INDEX

            for offset in range(num_models):
                model_idx = (start_idx + offset) % num_models
                model_name = GEMINI_MODEL_FALLBACKS[model_idx]

                for attempt in range(2):                                            
                    try:
                        res = self._run_gemini_api_loop(topic, opponent_last_claim, turn_number, ctx, model_name=model_name)
                        res["mode"] = "live"
                        res["model_used"] = model_name
                                                                                                           
                        GeminiAgent.CURRENT_MODEL_INDEX = model_idx
                        if model_name != GEMINI_MODEL:
                            logger.info(f"Used fallback model '{model_name}' (model index {model_idx}).")
                        return res
                    except Exception as e:
                        err_str = str(e)
                        if "429" in err_str or "quota" in err_str.lower():
                            if "GenerateRequestsPerDayPerProject" in err_str or "limit: 0" in err_str:
                                logger.warning(f"Daily quota exhausted for '{model_name}'. Trying next model in cycle...")
                                break
                            elif attempt == 0:
                                logger.warning(f"Per-minute rate limit on '{model_name}' (attempt 1/2). Waiting 5s...")
                                time.sleep(5)
                            else:
                                logger.warning(f"Rate limit persists on '{model_name}'. Trying next model in cycle...")
                                break
                        else:
                            logger.warning(f"Gemini API call failed on '{model_name}' ({e}). Trying next model in cycle...")
                            break
            logger.warning("All Gemini models in cycle exhausted or failed. Falling back to algorithmic agent loop.")

                                                       
        res = self._run_agentic_loop(topic, opponent_last_claim, turn_number, ctx)
        res["mode"] = "fallback"
        return res

    def _run_gemini_api_loop(
        self,
        topic: str,
        opponent_last_claim: str | None,
        turn_number: int,
        ctx: ExecutorContext,
        model_name: str = GEMINI_MODEL,
    ) -> dict[str, Any]:
        """Execute turn using google.generativeai SDK with tool calling."""
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        sys_instruction = (
            f"You are Agent A ({self.role}) in a logic-verified debate arena on the topic: '{topic}'. "
            "State your argument directly, naturally, and persuasively as a skilled debater. "
            "CRITICAL DIRECTIVE: Do NOT repeat the full topic title or problem statement string verbatim in your claim output text. "
            "Use natural domain vocabulary and subject concepts instead. "
            "You MUST call tools to ground your reasoning: "
            "1. Call `retrieve_relevant_fact` first to get a grounded fact. "
            "2. If responding to an opponent, call `select_best_rebuttal` with candidate options. "
            "3. Call `generate_claim` with the context, direction, and propositional form. "
            "4. Call `check_contradiction` with target='self' and target='combined'. "
            "Always follow tool outputs strictly."
        )

        prompt = (
            f"Turn {turn_number}. Topic: '{topic}'. "
            f"Opponent last claim: '{opponent_last_claim or 'None (Opening turn)'}'."
        )

        config = types.GenerateContentConfig(
            system_instruction=sys_instruction,
            tools=_prepare_gemini_tools(TOOL_SCHEMAS),
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        mcts_trace = None
        contradiction_result = {"found": False, "conflicting_clauses": [], "proof_steps": []}
        generated_claim = None

                                                      
        for _ in range(8):
            if not response.candidates or not response.candidates[0].content.parts:
                break

            part = response.candidates[0].content.parts[0]
            if not hasattr(part, "function_call") or not part.function_call:
                break

            fn_call = part.function_call
            fn_name = fn_call.name
            fn_args = dict(fn_call.args)

                                                    
            tool_res = execute_tool(fn_name, fn_args, ctx)

                            
            if fn_name == "select_best_rebuttal" and tool_res.success:
                mcts_trace = tool_res.output
            elif fn_name == "check_contradiction" and tool_res.success:
                contradiction_result = tool_res.output
            elif fn_name == "generate_claim" and tool_res.success:
                generated_claim = tool_res.output

                                                               
            tool_proto = genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=fn_name,
                    response=tool_res.output,
                )
            )
            response = chat.send_message(tool_proto)

                                                                                     
        if not generated_claim:
            res = self._run_agentic_loop(topic, opponent_last_claim, turn_number, ctx)
            res["mode"] = "fallback"
            return res

        raw_text = generated_claim.get("direction") or (response.text.strip() if response.text else f"Claim regarding {topic}")
        claim_text = clean_claim_text(raw_text)
        prop_form = generated_claim.get("propositional_form", "TopicClaim")

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
        grounding_fact = fact_res.output.get("top_fact", f"Evidence supports structured evaluation of {topic}.")

                                                                                         
        mcts_trace = None
        if self.agent_id == "agent_a":
            spoken = set(ctx.debate_state.own_claims)
        else:
            spoken = set(ctx.debate_state.opponent_claims)

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
        prop_form = f"{clean_topic}ProT{turn_number}"
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
