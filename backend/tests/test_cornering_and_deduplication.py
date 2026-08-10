"""
test_cornering_and_deduplication.py — Test zero-repetition argument pools, targeted rebuttals, and cornering points summary.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from fastapi.testclient import TestClient
import pytest

from main import app
from core.topic_knowledge import (
    get_topic_proposer_points,
    get_topic_opponent_points,
    get_targeted_rebuttal,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_argument_deduplication_and_targeted_rebuttals():
    topic = "should AI data centres be abolished"
    spoken = {"AI data centers provide the indispensable computational bedrock required for scientific breakthroughs, drug discovery, and climate modeling."}

    pro_points = get_topic_proposer_points(topic, spoken)
    # Ensure spoken claim is excluded
    assert spoken.pop() not in pro_points
    assert len(pro_points) >= 15

    # Test targeted rebuttal lookup
    opponent_claim = "Cooling massive AI server clusters consumes millions of gallons of local drinking water daily."
    rebuttal = get_targeted_rebuttal(topic, opponent_claim, "proposer")
    assert rebuttal is not None
    assert "water" in rebuttal.lower() or "cooling" in rebuttal.lower() or "closed-loop" in rebuttal.lower()


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
        txt = turn_resp.json()["claim"]["text"]
        claims_spoken.append(txt)

    # Verify all claims across 10 turns are unique (no duplicates)
    assert len(claims_spoken) == len(set(claims_spoken)), f"Duplicate claims found: {claims_spoken}"

    # Verify summary has cornering points
    sum_resp = client.get(f"/summary/{debate_id}")
    assert sum_resp.status_code == 200
    summary = sum_resp.json()
    assert "cornering_points" in summary
    assert len(summary["cornering_points"]) > 0

    cp = summary["cornering_points"][0]
    assert "point" in cp
    assert "why_dangerous" in cp
    assert "best_reply" in cp
