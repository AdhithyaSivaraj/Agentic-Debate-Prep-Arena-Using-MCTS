import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from fastapi.testclient import TestClient
import pytest

from main import app


@pytest.fixture
def client():
    return TestClient(app)


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

    # Session is complete once the turn limit is hit; the summary is built lazily by /summary
    trans_resp = client.get(f"/transcript/{debate_id}")
    assert trans_resp.status_code == 200
    assert trans_resp.json()["status"] == "complete"

    summary_resp = client.get(f"/summary/{debate_id}")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["debate_id"] == debate_id
    assert summary["topic"] == topic
    assert summary["total_turns"] == 4
    assert "winner" in summary
    assert "verdict_statement" in summary

    # The generated summary is now attached to the transcript
    assert client.get(f"/transcript/{debate_id}").json()["summary"] is not None


def test_summary_is_grounded_and_plain_english(client):
    debate_id = client.post("/start-debate", json={"topic": "Should cities ban cars?", "max_turns": 4}).json()["debate_id"]
    turns = [client.post("/next-turn", json={"debate_id": debate_id}).json() for _ in range(4)]
    summary = client.get(f"/summary/{debate_id}").json()

    # Debrief fields are split into attack / defense and leaked atom names are rewritten as words
    assert summary["proposer_cornered_analysis"].startswith('Attack: "')
    assert "\nDefense: " in summary["proposer_cornered_analysis"]
    assert "OutcomesImprove" not in summary["proposer_cornered_analysis"]
    assert "outcomes improve" in summary["proposer_cornered_analysis"]

    # The verdict reasoning reports exactly what resolution proved
    a_refutes = sum(t["claim"]["refutes_opponent"] for t in turns if t["claim"]["speaker"] == "agent_a")
    assert f"Agent A (Proposer) proved {a_refutes} refutation(s)" in summary["winner_reasoning"]

    # Each cornering point's escape route is the attacker's comeback, generated per point
    for cp in summary["cornering_points"]:
        assert cp["point"] in [t["claim"]["text"] for t in turns]
        assert cp["escape_route"]


def test_humanize_logic():
    from llm_client import humanize_logic
    out = humanize_logic("So LabSecurityWired → EthernetLatencyLow, and ¬CostsHigh.", {"LabSecurityWired", "EthernetLatencyLow", "CostsHigh"})
    assert out == "So lab security wired leads to ethernet latency low, and not costs high."
