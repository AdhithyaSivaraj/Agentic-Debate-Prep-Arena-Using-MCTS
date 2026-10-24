"""
conftest.py — Offline test harness.

Every LLM call in the backend goes through llm_client.complete(). This autouse fixture
replaces it with a deterministic fake, so the suite never touches the network and the
algorithms (resolution, MCTS, retrieval) run for real on predictable LLM output.
"""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest

import llm_client


FAKE_FACTS = [
    {"text": "Adopting the policy improves measured outcomes in pilot programs.", "propositional": "PolicyAdopted → OutcomesImprove", "relationship": "supports_proposition"},
    {"text": "Improved outcomes reduce long-term public costs.", "propositional": "OutcomesImprove → CostsFall", "relationship": "supports_proposition"},
    {"text": "The policy has been adopted successfully in several regions.", "propositional": "PolicyAdopted", "relationship": "supports_proposition"},
    {"text": "Broad public support makes implementation feasible.", "propositional": "PublicSupport", "relationship": "supports_proposition"},
    {"text": "Implementation requires large upfront spending.", "propositional": "PolicyAdopted → UpfrontSpendingHigh", "relationship": "contradicts_proposition"},
    {"text": "High upfront spending crowds out other priorities.", "propositional": "UpfrontSpendingHigh → PrioritiesCrowdedOut", "relationship": "contradicts_proposition"},
    {"text": "Independent audits found no lasting outcome improvement.", "propositional": "¬OutcomesImprove", "relationship": "contradicts_proposition"},
    {"text": "Rollouts frequently face administrative delays.", "propositional": "AdministrativeDelays", "relationship": "contradicts_proposition"},
    {"text": "Outcome data is collected by independent agencies.", "propositional": "DataIndependent", "relationship": "is_independent"},
]

CANDIDATE_FORMS = ["¬OutcomesImprove", "OutcomesImprove", "¬CostsFall", "PublicSupport → PolicyAdopted"]
ISSUES = ["outcomes", "outcomes", "cost", "public support"]


class FakeLLM:
    """Deterministic stand-in for llm_client.complete(); set fail_on to simulate outages."""

    def __init__(self):
        self.calls: list[str] = []
        self.fail_on: set[str] = set()
        self._candidate_round = 0

    def __call__(self, model_name, system, user, *args, **kwargs):
        kind = self._kind(user)
        self.calls.append(kind)
        if kind in self.fail_on or "all" in self.fail_on:
            raise llm_client.LLMUnavailable(f"fake outage for {kind}")
        if kind == "frame":
            return json.dumps({
                "resolution": "Cities should adopt the policy.",
                "proposer_position": "The policy should be adopted.",
                "opponent_position": "The policy should not be adopted.",
            })
        if kind == "facts":
            return json.dumps({"facts": FAKE_FACTS})
        if kind == "candidates":
            self._candidate_round += 1
            r = self._candidate_round
            role = "proposer" if "YOU are the Proposer" in user else "opponent"
            return json.dumps({"plan": "Rebut, then open a new issue.", "candidates": [
                {"claim": f"Round {r} argument {i}: evidence on point {form} decides this.", "propositional": form,
                 "issue": ISSUES[i], "helps": role}
                for i, form in enumerate(CANDIDATE_FORMS)
            ]})
        if kind == "debrief":
            return json.dumps({
                "verdict_statement": "The winning side forced the decisive contradiction.",
                "proposer_toughest_attack": "Audits found no lasting outcome improvement.",
                "proposer_defense": "The pilot data shows OutcomesImprove across every region.",
                "opponent_trap": "Pilots improved outcomes.",
                "opponent_escape_route": "The pilots were not representative of national rollouts.",
                "key_proposer_points": ["Pilots improved outcomes."],
                "key_opponent_points": ["Audits found no lasting gains."],
            })
        return "A concrete counter-argument grounded in the pilot data."

    @staticmethod
    def _kind(user: str) -> str:
        if "Rewrite it as a debate" in user:
            return "frame"
        if "Generate exactly" in user:
            return "facts"
        if "candidate arguments" in user:
            return "candidates"
        if "post-debate debrief" in user:
            return "debrief"
        return "counter"


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(llm_client, "complete", fake)
    return fake
