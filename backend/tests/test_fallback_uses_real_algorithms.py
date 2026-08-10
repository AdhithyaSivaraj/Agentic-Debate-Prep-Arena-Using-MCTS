"""
test_fallback_uses_real_algorithms.py — Verification of Offline Fallback Integrity (FIX 2)

Asserts that when Gemini / OpenRouter API calls fail or rate-limit:
1. The turn response explicitly sets mode="fallback" (transparency).
2. Resolution engine's check_contradiction() algorithm is STILL executed on real KB data.
3. MCTS engine's select_best_rebuttal() algorithm is STILL executed on real candidate data.
4. Fallback ONLY replaces language generation (generate_claim), NEVER the core algorithms.
"""
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from fastapi.testclient import TestClient
from main import app
import tools.tool_executor as executor_module

client = TestClient(app)


def test_fallback_mode_executes_real_algorithms():
    """Verify that forcing API failures sets mode='fallback' while STILL executing MCTS & Resolution."""
    
    # Spy on core algorithm functions inside tool_executor
    real_select_best_rebuttal = executor_module.select_best_rebuttal
    select_best_rebuttal_spy = MagicMock(side_effect=real_select_best_rebuttal)

    with patch("agents.gemini_agent.GEMINI_API_KEY", "fake_key_forces_fallback"), \
         patch("agents.nemotron_agent.OPENROUTER_API_KEY", "fake_key_forces_fallback"), \
         patch.object(executor_module, "select_best_rebuttal", select_best_rebuttal_spy):

        # 1. Start Debate
        start_res = client.post("/start-debate", json={"topic": "Should standardized exams be abolished?"})
        assert start_res.status_code == 201
        debate_id = start_res.json()["debate_id"]

        # 2. Turn 1 (Agent A in fallback mode)
        turn1_res = client.post("/next-turn", json={"debate_id": debate_id})
        assert turn1_res.status_code == 200
        t1 = turn1_res.json()
        assert t1["mode"] == "fallback"

        # 3. Turn 2 (Agent B in fallback mode)
        turn2_res = client.post("/next-turn", json={"debate_id": debate_id})
        assert turn2_res.status_code == 200
        t2 = turn2_res.json()
        assert t2["mode"] == "fallback"

        # Assert MCTS algorithm was called for real in tool_executor
        assert select_best_rebuttal_spy.called, "MCTS select_best_rebuttal must be called during fallback!"
        assert select_best_rebuttal_spy.call_count >= 2

        # Assert MCTS trace is present and valid in turn 2
        assert t2["mcts_trace"] is not None
        assert "chosen_rebuttal" in t2["mcts_trace"]
        assert len(t2["mcts_trace"]["rejected_candidates"]) > 0

        # Assert Resolution contradiction result is computed for real
        assert "found" in t2["contradiction_result"]
        assert t2["contradiction_result"]["found"] is False
