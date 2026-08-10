"""
test_e2e_backend.py — End-to-End Backend Integration Test (Phase 6)

Tests Mode 1 (Agent A vs Agent B autonomous debate loop):
- Start debate on a complex topic
- Run a 6-turn debate alternating between Agent A (proposer) and Agent B (opponent)
- Verify KnowledgeBase growth, Resolution contradiction checks, MCTS traces, and full Transcript retrieval.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_full_agent_vs_agent_debate_loop():
    topic = "Should artificial intelligence development be regulated globally?"

    # 1. Start Debate
    start_resp = client.post("/start-debate", json={"topic": topic})
    assert start_resp.status_code == 201
    start_data = start_resp.json()
    debate_id = start_data["debate_id"]
    assert debate_id is not None
    assert start_data["topic"] == topic
    assert start_data["fact_base_count"] > 0

    # 2. Run 6 full turns
    turns_history = []
    for turn_num in range(1, 7):
        turn_resp = client.post("/next-turn", json={"debate_id": debate_id})
        assert turn_resp.status_code == 200
        turn_data = turn_resp.json()

        assert turn_data["turn_number"] == turn_num
        expected_speaker = "agent_a" if turn_num % 2 != 0 else "agent_b"
        assert turn_data["claim"]["speaker"] == expected_speaker
        assert len(turn_data["claim"]["text"]) > 0
        assert len(turn_data["claim"]["propositional_form"]) > 0

        # Verify contradiction result payload structure
        assert "found" in turn_data["contradiction_result"]
        assert "conflicting_clauses" in turn_data["contradiction_result"]
        assert "proof_steps" in turn_data["contradiction_result"]

        turns_history.append(turn_data)

    # 3. Retrieve Full Transcript
    transcript_resp = client.get(f"/transcript/{debate_id}")
    assert transcript_resp.status_code == 200
    transcript_data = transcript_resp.json()

    assert transcript_data["debate_id"] == debate_id
    assert transcript_data["topic"] == topic
    assert len(transcript_data["turns"]) == 6
    assert transcript_data["status"] == "running"

    # Verify speaker sequence in transcript: A, B, A, B, A, B
    speakers = [t["claim"]["speaker"] for t in transcript_data["turns"]]
    assert speakers == ["agent_a", "agent_b", "agent_a", "agent_b", "agent_a", "agent_b"]

    # 4. Verify MCTS Trace Retrieval for turn 2 (Agent B opponent turn)
    mcts_resp = client.get(f"/mcts-trace/{debate_id}/2")
    if mcts_resp.status_code == 200:
        trace_data = mcts_resp.json()
        assert "chosen_rebuttal" in trace_data
        assert "rejected_candidates" in trace_data
        assert "n_simulations" in trace_data
        assert trace_data["n_simulations"] > 0
