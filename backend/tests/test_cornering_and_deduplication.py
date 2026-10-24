"""
test_cornering_and_deduplication.py — No repeated claims across turns, and cornering points in the summary.
"""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_zero_repetition_across_many_turns(client):
    topic = "should AI data centres be abolished"
    max_turns = 10

    start_resp = client.post("/start-debate", json={"topic": topic, "max_turns": max_turns})
    assert start_resp.status_code == 201
    debate_id = start_resp.json()["debate_id"]

    claims_spoken = []
    for _ in range(max_turns):
        turn_resp = client.post("/next-turn", json={"debate_id": debate_id})
        assert turn_resp.status_code == 200
        claims_spoken.append(turn_resp.json()["claim"]["text"])

    assert len(claims_spoken) == len(set(claims_spoken)), f"Duplicate claims found: {claims_spoken}"

    sum_resp = client.get(f"/summary/{debate_id}")
    assert sum_resp.status_code == 200
    summary = sum_resp.json()
    assert len(summary["cornering_points"]) > 0
    cp = summary["cornering_points"][0]
    assert cp["point"] in claims_spoken
    assert cp["why_dangerous"]
    assert cp["best_reply"]


def test_fallback_candidates_do_not_repeat(client, fake_llm):
    fake_llm.fail_on = {"candidates", "counter", "debrief"}
    start_resp = client.post("/start-debate", json={"topic": "Should cities ban cars?", "max_turns": 6})
    debate_id = start_resp.json()["debate_id"]

    claims = [client.post("/next-turn", json={"debate_id": debate_id}).json()["claim"]["text"] for _ in range(6)]
    for speaker_claims in (claims[0::2], claims[1::2]):
        assert len(speaker_claims) == len(set(speaker_claims))


def test_opening_claim_cannot_refute(client):
    debate_id = client.post("/start-debate", json={"topic": "Should cities ban cars?"}).json()["debate_id"]
    first = client.post("/next-turn", json={"debate_id": debate_id}).json()
    assert first["claim"]["refutes_opponent"] is False
    assert first["clash_result"]["found"] is False


def test_refutation_points_at_the_refuted_turn(client):
    debate_id = client.post("/start-debate", json={"topic": "Should cities ban cars?", "max_turns": 8}).json()["debate_id"]
    turns = [client.post("/next-turn", json={"debate_id": debate_id}).json() for _ in range(8)]
    refutations = [t for t in turns if t["claim"]["refutes_opponent"]]
    assert refutations, "fake debate should produce at least one refutation"
    for t in refutations:
        target = t["claim"]["refutes_turn"]
        if target is not None:
            assert target < t["turn_number"]
            assert turns[target - 1]["claim"]["speaker"] != t["claim"]["speaker"]


def test_debate_is_framed_with_explicit_positions(client):
    res = client.post("/start-debate", json={"topic": "Gaming laptop or business laptop for students?"}).json()
    assert res["resolution"] and res["proposer_position"] and res["opponent_position"]
    transcript = client.get(f"/transcript/{res['debate_id']}").json()
    assert transcript["proposer_position"] == res["proposer_position"]


def test_candidates_helping_the_other_side_are_dropped(client, fake_llm, monkeypatch):
    import json
    real_call = fake_llm.__class__.__call__

    def call(self, model_name, system, user, *args, **kw):
        if "candidate arguments" in user:
            return json.dumps({"candidates": [
                {"claim": "The other side is right about cost.", "propositional": "CostsFall", "issue": "cost", "helps": "opponent"},
                {"claim": "Pilot results favour adoption.", "propositional": "OutcomesImprove", "issue": "outcomes", "helps": "proposer"},
            ]})
        return real_call(self, model_name, system, user, *args, **kw)

    monkeypatch.setattr(fake_llm.__class__, "__call__", call)
    debate_id = client.post("/start-debate", json={"topic": "Should cities ban cars?"}).json()["debate_id"]
    turn = client.post("/next-turn", json={"debate_id": debate_id}).json()
    assert turn["claim"]["text"] == "Pilot results favour adoption."
    assert turn["claim"]["issue"] == "outcomes"
    assert all(c["text"] != "The other side is right about cost." for c in turn["mcts_trace"]["rejected_candidates"])
