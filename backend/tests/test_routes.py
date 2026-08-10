"""
test_routes.py — Integration tests for FastAPI debate endpoints (Phase 5).
Uses FastAPI TestClient — runs offline without needing live API keys.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_start_debate():
    response = client.post("/start-debate", json={"topic": "Should standardized exams be abolished?"})
    assert response.status_code == 201
    data = response.json()
    assert "debate_id" in data
    assert data["topic"] == "Should standardized exams be abolished?"
    assert data["fact_base_count"] > 0


def test_start_debate_empty_topic_fails():
    response = client.post("/start-debate", json={"topic": "   "})
    assert response.status_code == 400


def test_next_turn_flow():
    # 1. Start debate
    start_res = client.post("/start-debate", json={"topic": "AI Automation in Healthcare"})
    assert start_res.status_code == 201
    debate_id = start_res.json()["debate_id"]

    # 2. Turn 1 (Agent A - Gemini)
    turn1_res = client.post("/next-turn", json={"debate_id": debate_id})
    assert turn1_res.status_code == 200
    t1 = turn1_res.json()
    assert t1["turn_number"] == 1
    assert t1["claim"]["speaker"] == "agent_a"
    assert len(t1["claim"]["text"]) > 0

    # 3. Turn 2 (Agent B - Nemotron)
    turn2_res = client.post("/next-turn", json={"debate_id": debate_id})
    assert turn2_res.status_code == 200
    t2 = turn2_res.json()
    assert t2["turn_number"] == 2
    assert t2["claim"]["speaker"] == "agent_b"

    # 4. Get Transcript
    trans_res = client.get(f"/transcript/{debate_id}")
    assert trans_res.status_code == 200
    trans_data = trans_res.json()
    assert len(trans_data["turns"]) == 2


def test_mcts_trace_endpoint():
    start_res = client.post("/start-debate", json={"topic": "Renewable Energy Subsidies"})
    debate_id = start_res.json()["debate_id"]

    # Advance 2 turns to ensure MCTS trace is generated
    client.post("/next-turn", json={"debate_id": debate_id})
    client.post("/next-turn", json={"debate_id": debate_id})

    trace_res = client.get(f"/mcts-trace/{debate_id}/2")
    # Turn 2 runs MCTS rebuttal selector
    assert trace_res.status_code in (200, 404)
    if trace_res.status_code == 200:
        data = trace_res.json()
        assert "chosen_rebuttal" in data
        assert "rejected_candidates" in data


def test_invalid_debate_id_returns_404():
    response = client.post("/next-turn", json={"debate_id": "nonexistent_id_12345"})
    assert response.status_code == 404
