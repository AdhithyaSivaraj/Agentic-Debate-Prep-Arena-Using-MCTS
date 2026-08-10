"""
test_fallback_topic_alignment.py — Unit test for topic fallback alignment and on-demand session isolation.
"""
from fastapi.testclient import TestClient
import pytest

from main import app
from api.routes_debate import DEBATE_SESSIONS


@pytest.fixture
def client():
    return TestClient(app)


def test_fallback_topic_alignment(client):
    topic = "should AI data centres be abolished"

    # Start a debate
    start_resp = client.post("/start-debate", json={"topic": topic})
    assert start_resp.status_code == 201
    debate_id = start_resp.json()["debate_id"]

    # Verify session is created on-demand for this topic
    assert debate_id in DEBATE_SESSIONS
    assert DEBATE_SESSIONS[debate_id]["topic"] == topic

    # Turn 1: Agent A (Proposer fallback)
    turn1_resp = client.post("/next-turn", json={"debate_id": debate_id})
    assert turn1_resp.status_code == 200
    t1_claim = turn1_resp.json()["claim"]["text"].lower()

    # Check that t1_claim does NOT contain exam references
    assert "exam" not in t1_claim
    assert "standardized assessment" not in t1_claim
    assert "testing" not in t1_claim

    # Turn 2: Agent B (Opponent fallback)
    turn2_resp = client.post("/next-turn", json={"debate_id": debate_id})
    assert turn2_resp.status_code == 200
    t2_claim = turn2_resp.json()["claim"]["text"].lower()

    # Check that t2_claim does NOT contain exam references
    assert "exam" not in t2_claim
    assert "standardized assessment" not in t2_claim
    assert "testing" not in t2_claim


def test_on_demand_session_isolation(client):
    topic = "should AI data centres be abolished"

    # Start a new debate session on the topic
    start_resp = client.post("/start-debate", json={"topic": topic})
    assert start_resp.status_code == 201
    debate_id = start_resp.json()["debate_id"]

    # Verify session has isolated facts built specifically for this debate
    sess = DEBATE_SESSIONS[debate_id]
    assert len(sess["fact_texts"]) > 0
    assert sess["topic"] == topic
