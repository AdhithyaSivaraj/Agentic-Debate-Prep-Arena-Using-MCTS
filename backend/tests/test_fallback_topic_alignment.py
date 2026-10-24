"""
test_fallback_topic_alignment.py — Per-debate session isolation of the generated fact base.
"""
import pytest
from fastapi.testclient import TestClient

from api.routes_debate import DEBATE_SESSIONS
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_on_demand_session_isolation(client):
    topic = "should AI data centres be abolished"

    start_resp = client.post("/start-debate", json={"topic": topic})
    assert start_resp.status_code == 201
    debate_id = start_resp.json()["debate_id"]

    sess = DEBATE_SESSIONS[debate_id]
    assert len(sess["fact_texts"]) > 0
    assert sess["topic"] == topic
    assert sess["vocabulary"]


def test_knowledge_bases_seeded_by_side(client):
    debate_id = client.post("/start-debate", json={"topic": "Should cities ban cars?"}).json()["debate_id"]
    sess = DEBATE_SESSIONS[debate_id]
    a_facts = set(sess["agent_a"].kb.get_history())
    b_facts = set(sess["agent_b"].kb.get_history())
    for fact in sess["fact_records"]:
        if fact.relationship == "supports_proposition":
            assert fact.text in a_facts and fact.text not in b_facts
        elif fact.relationship == "contradicts_proposition":
            assert fact.text in b_facts and fact.text not in a_facts
        else:
            assert fact.text in a_facts and fact.text in b_facts


def test_inconsistent_seed_facts_are_skipped(client, fake_llm, monkeypatch):
    import json
    from tests.conftest import FAKE_FACTS
    conflicting = FAKE_FACTS + [{"text": "Public support is absent.", "propositional": "¬PublicSupport", "relationship": "supports_proposition"}]
    real_call = fake_llm.__class__.__call__

    def call(self, model_name, system, user, *args, **kw):
        if "Generate exactly" in user:
            return json.dumps({"facts": conflicting})
        return real_call(self, model_name, system, user, *args, **kw)

    monkeypatch.setattr(fake_llm.__class__, "__call__", call)
    debate_id = client.post("/start-debate", json={"topic": "Should cities ban cars?"}).json()["debate_id"]
    kb = DEBATE_SESSIONS[debate_id]["agent_a"].kb
    assert kb.ask_contradiction().found is False
    assert "Public support is absent." not in kb.get_history()


def test_self_contradicting_claim_is_retracted():
    from core.knowledge_base import KnowledgeBase
    from core.resolution import atom, neg_atom

    kb = KnowledgeBase("agent_a")
    kb.tell(atom("P"))
    kb.tell(neg_atom("P"))
    assert kb.ask_contradiction().found is True
    kb.retract(neg_atom("P"))
    assert kb.ask_contradiction().found is False
