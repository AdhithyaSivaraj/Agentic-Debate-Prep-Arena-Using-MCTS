"""
test_fallback_uses_real_algorithms.py — Verification of Offline Fallback Integrity

When candidate generation fails mid-debate:
1. The turn is marked mode="fallback" (transparency).
2. Candidates come from the agent's side of the generated fact base — never from scripts.
3. MCTS and resolution still execute on real KB data.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

import core.mcts as mcts_module
from api.routes_debate import DEBATE_SESSIONS
from tests.conftest import FAKE_FACTS
from main import app

client = TestClient(app)


def test_fallback_mode_executes_real_algorithms(fake_llm):
    fake_llm.fail_on = {"candidates"}
    start_res = client.post("/start-debate", json={"topic": "Should standardized exams be abolished?"})
    assert start_res.status_code == 201
    debate_id = start_res.json()["debate_id"]

    with patch.object(mcts_module.MCTS, "run", autospec=True, side_effect=mcts_module.MCTS.run) as run_spy:
        t1 = client.post("/next-turn", json={"debate_id": debate_id}).json()
        t2 = client.post("/next-turn", json={"debate_id": debate_id}).json()

    assert t1["mode"] == "fallback" and t2["mode"] == "fallback"
    assert run_spy.call_count == 2

    fact_texts = {f["text"] for f in FAKE_FACTS}
    supporting = {f["text"] for f in FAKE_FACTS if f["relationship"] != "contradicts_proposition"}
    opposing = {f["text"] for f in FAKE_FACTS if f["relationship"] != "supports_proposition"}
    assert t1["claim"]["text"] in supporting
    assert t2["claim"]["text"] in opposing
    assert t1["claim"]["text"] in fact_texts

    assert t2["mcts_trace"]["rejected_candidates"]
    assert "found" in t2["contradiction_result"]
    assert "found" in t2["clash_result"]
    assert DEBATE_SESSIONS[debate_id]["agent_b"].kb.get_opponent_clauses()


def test_start_fails_without_any_llm(fake_llm):
    fake_llm.fail_on = {"all"}
    res = client.post("/start-debate", json={"topic": "Should cities ban cars?"})
    assert res.status_code == 503
