import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from fastapi.testclient import TestClient
import pytest

from main import app
from core.topic_knowledge import get_topic_grounded_facts, get_topic_proposer_points, get_topic_opponent_points


@pytest.fixture
def client():
    return TestClient(app)


def test_topic_knowledge_concrete_points():
    topic = "should AI data centres be abolished"
    facts = get_topic_grounded_facts(topic)
    assert len(facts) >= 4

    pro_args = get_topic_proposer_points(topic)
    con_args = get_topic_opponent_points(topic)

    assert len(pro_args) >= 5
    assert len(con_args) >= 5


def test_clean_claims_and_max_turns_summary(client):
    topic = "should AI data centres be abolished"
    max_turns = 4

    # Start debate with max_turns=4
    start_resp = client.post("/start-debate", json={"topic": topic, "max_turns": max_turns})
    assert start_resp.status_code == 201
    debate_id = start_resp.json()["debate_id"]
    assert start_resp.json()["max_turns"] == 4

    # Execute 4 turns
    for t in range(1, max_turns + 1):
        turn_resp = client.post("/next-turn", json={"debate_id": debate_id})
        assert turn_resp.status_code == 200
        claim_text = turn_resp.json()["claim"]["text"]
        # Verify no "(Grounded in: '...')" inline text
        assert "(Grounded in:" not in claim_text

    # Turn 5 should be rejected due to max_turns limit
    over_turn_resp = client.post("/next-turn", json={"debate_id": debate_id})
    assert over_turn_resp.status_code == 400
    assert "limit" in over_turn_resp.json()["detail"].lower() or "complete" in over_turn_resp.json()["detail"].lower()

    # Check transcript session status is complete
    trans_resp = client.get(f"/transcript/{debate_id}")
    assert trans_resp.status_code == 200
    assert trans_resp.json()["status"] == "complete"
    assert trans_resp.json()["summary"] is not None

    # Fetch summary endpoint directly
    summary_resp = client.get(f"/summary/{debate_id}")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["debate_id"] == debate_id
    assert summary["topic"] == topic
    assert summary["total_turns"] == 4
    assert "winner" in summary
    assert "verdict_statement" in summary
