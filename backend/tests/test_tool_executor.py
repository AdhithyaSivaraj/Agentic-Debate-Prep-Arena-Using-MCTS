"""
test_tool_executor.py — Unit tests for tool_executor.py
Phase 4: all tests use fake KB, fake embed_fn, and a pre-built FactIndex.
No real API calls, no LLM calls, no network access.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
import numpy as np

from core.resolution import atom, neg_atom, implication_to_clause
from core.knowledge_base import KnowledgeBase
from core.retrieval import FactIndex
from core.mcts import DebateState
from tools.tool_executor import (
    ExecutorContext,
    ToolResult,
    execute_tool,
    parse_propositional_form,
    get_available_tool_names,
)


# ===========================================================================
# Helpers
# ===========================================================================

def make_fake_embed_fn(dim: int = 3):
    """Fake embed function: returns identity basis vectors cyclically."""
    counter = [0]
    def embed_fn(texts: list[str]) -> np.ndarray:
        vecs = []
        for _ in texts:
            vec = np.zeros(dim)
            vec[counter[0] % dim] = 1.0
            counter[0] += 1
            vecs.append(vec)
        return np.array(vecs, dtype=float)
    return embed_fn


def make_test_context(topic_facts: list[str] | None = None) -> ExecutorContext:
    """Build a minimal ExecutorContext for testing (no API calls)."""
    facts = topic_facts or ["Exams cause stress", "Abolishing exams reduces pressure", "Grades motivate students"]
    dim = 3
    # Build a simple deterministic FactIndex
    vectors = np.eye(len(facts), dim, dtype=float)
    fact_index = FactIndex(facts=facts, vectors=vectors)

    embed_fn = make_fake_embed_fn(dim)
    agent_kb = KnowledgeBase("agent_a")
    opponent_kb = KnowledgeBase("agent_b")
    debate_state = DebateState()

    return ExecutorContext(
        agent_kb=agent_kb,
        opponent_kb=opponent_kb,
        embed_fn=embed_fn,
        fact_index=fact_index,
        debate_state=debate_state,
        n_simulations=10,
        agent_id="agent_a",
    )


# ===========================================================================
# Tests for parse_propositional_form
# ===========================================================================

class TestParsePropositionalForm:
    def test_implication_arrow(self):
        clause = parse_propositional_form("A → B")
        assert clause == implication_to_clause("A", "B")

    def test_implication_ascii_arrow(self):
        clause = parse_propositional_form("P -> Q")
        assert clause == implication_to_clause("P", "Q")

    def test_positive_atom(self):
        clause = parse_propositional_form("ExamsHarmful")
        assert clause == atom("ExamsHarmful")

    def test_negation_unicode(self):
        clause = parse_propositional_form("¬StressHigh")
        assert clause == neg_atom("StressHigh")

    def test_negation_english(self):
        clause = parse_propositional_form("NOT StressHigh")
        assert clause == neg_atom("StressHigh")

    def test_implication_with_spaces(self):
        clause = parse_propositional_form("  ExamsAbolished  →  StressLow  ")
        assert clause == implication_to_clause("ExamsAbolished", "StressLow")

    def test_unparseable_returns_none(self):
        result = parse_propositional_form("this is not a valid form with multiple spaces")
        assert result is None

    def test_empty_string_returns_none(self):
        result = parse_propositional_form("")
        assert result is None


# ===========================================================================
# Tests for execute_tool dispatch
# ===========================================================================

class TestGetAvailableToolNames:
    def test_all_four_tools_registered(self):
        names = set(get_available_tool_names())
        assert names == {
            "retrieve_relevant_fact",
            "check_contradiction",
            "select_best_rebuttal",
            "generate_claim",
        }


class TestExecuteToolUnknown:
    def test_unknown_tool_returns_failure(self):
        ctx = make_test_context()
        result = execute_tool("nonexistent_tool", {}, ctx)
        assert result.success is False
        assert "Unknown tool" in result.error

    def test_unknown_tool_result_has_tool_name(self):
        ctx = make_test_context()
        result = execute_tool("bad_tool", {}, ctx)
        assert result.tool_name == "bad_tool"


class TestRetrieveRelevantFact:
    def test_success_with_valid_args(self):
        ctx = make_test_context()
        result = execute_tool("retrieve_relevant_fact", {"claim_topic": "exams stress"}, ctx)
        assert result.success is True
        assert result.tool_name == "retrieve_relevant_fact"

    def test_output_has_top_fact(self):
        ctx = make_test_context()
        result = execute_tool("retrieve_relevant_fact", {"claim_topic": "exams stress"}, ctx)
        assert "top_fact" in result.output
        assert isinstance(result.output["top_fact"], str)

    def test_output_has_retrieved_facts_list(self):
        ctx = make_test_context()
        result = execute_tool("retrieve_relevant_fact", {"claim_topic": "exams"}, ctx)
        assert "retrieved_facts" in result.output
        assert isinstance(result.output["retrieved_facts"], list)

    def test_missing_claim_topic_returns_failure(self):
        ctx = make_test_context()
        result = execute_tool("retrieve_relevant_fact", {}, ctx)
        assert result.success is False

    def test_top_k_parameter_respected(self):
        ctx = make_test_context()
        result = execute_tool(
            "retrieve_relevant_fact",
            {"claim_topic": "exams", "top_k": 2},
            ctx,
        )
        assert result.success is True
        assert len(result.output["retrieved_facts"]) <= 2

    def test_to_llm_message_is_json_string(self):
        ctx = make_test_context()
        result = execute_tool("retrieve_relevant_fact", {"claim_topic": "exams"}, ctx)
        import json
        msg = result.to_llm_message()
        parsed = json.loads(msg)   # must be valid JSON
        assert "top_fact" in parsed


class TestCheckContradiction:
    def test_self_check_no_contradiction(self):
        """Empty KB → no contradiction."""
        ctx = make_test_context()
        result = execute_tool(
            "check_contradiction",
            {"target": "self", "agent_id": "agent_a"},
            ctx,
        )
        assert result.success is True
        assert result.output["found"] is False

    def test_self_check_finds_contradiction(self):
        """KB with P and ¬P → contradiction found."""
        ctx = make_test_context()
        ctx.agent_kb.tell(atom("P"))
        ctx.agent_kb.tell(neg_atom("P"))
        result = execute_tool(
            "check_contradiction",
            {"target": "self", "agent_id": "agent_a"},
            ctx,
        )
        assert result.success is True
        assert result.output["found"] is True

    def test_opponent_check_no_contradiction(self):
        ctx = make_test_context()
        result = execute_tool(
            "check_contradiction",
            {"target": "opponent", "agent_id": "agent_a"},
            ctx,
        )
        assert result.success is True
        assert result.output["found"] is False

    def test_combined_check_cross_agent_contradiction(self):
        ctx = make_test_context()
        ctx.agent_kb.tell(atom("P"))
        ctx.agent_kb.tell_opponent(neg_atom("P"))
        result = execute_tool(
            "check_contradiction",
            {"target": "combined", "agent_id": "agent_a"},
            ctx,
        )
        assert result.success is True
        assert result.output["found"] is True

    def test_invalid_target_returns_failure(self):
        ctx = make_test_context()
        result = execute_tool(
            "check_contradiction",
            {"target": "invalid_target", "agent_id": "agent_a"},
            ctx,
        )
        assert result.success is False

    def test_output_has_proof_steps(self):
        ctx = make_test_context()
        ctx.agent_kb.tell(atom("P"))
        ctx.agent_kb.tell(neg_atom("P"))
        result = execute_tool(
            "check_contradiction",
            {"target": "self", "agent_id": "agent_a"},
            ctx,
        )
        assert "proof_steps" in result.output
        assert isinstance(result.output["proof_steps"], list)

    def test_output_has_summary(self):
        ctx = make_test_context()
        result = execute_tool(
            "check_contradiction",
            {"target": "self", "agent_id": "agent_a"},
            ctx,
        )
        assert "summary" in result.output
        assert isinstance(result.output["summary"], str)


class TestSelectBestRebuttal:
    def test_success_with_valid_candidates(self):
        ctx = make_test_context()
        result = execute_tool(
            "select_best_rebuttal",
            {"candidates": ["A", "B", "C"], "agent_id": "agent_a"},
            ctx,
        )
        assert result.success is True

    def test_chosen_rebuttal_from_candidates(self):
        ctx = make_test_context()
        candidates = ["Rebuttal X", "Rebuttal Y", "Rebuttal Z"]
        result = execute_tool(
            "select_best_rebuttal",
            {"candidates": candidates, "agent_id": "agent_a"},
            ctx,
        )
        assert result.output["chosen_rebuttal"] in candidates

    def test_rejected_candidates_returned(self):
        ctx = make_test_context()
        result = execute_tool(
            "select_best_rebuttal",
            {"candidates": ["A", "B", "C"], "agent_id": "agent_a"},
            ctx,
        )
        assert "rejected_candidates" in result.output
        assert isinstance(result.output["rejected_candidates"], list)

    def test_empty_candidates_returns_failure(self):
        ctx = make_test_context()
        result = execute_tool(
            "select_best_rebuttal",
            {"candidates": [], "agent_id": "agent_a"},
            ctx,
        )
        assert result.success is False

    def test_n_simulations_in_output(self):
        ctx = make_test_context()
        result = execute_tool(
            "select_best_rebuttal",
            {"candidates": ["A", "B"], "agent_id": "agent_a", "n_simulations": 5},
            ctx,
        )
        assert result.output["n_simulations"] == 5


class TestGenerateClaim:
    def test_success_with_valid_args(self):
        ctx = make_test_context()
        result = execute_tool(
            "generate_claim",
            {
                "context": "Topic: exams. Role: proposer.",
                "direction": "Exams cause stress",
                "propositional_form": "Exams → Stress",
                "agent_id": "agent_a",
            },
            ctx,
        )
        assert result.success is True

    def test_valid_propositional_form_updates_kb(self):
        ctx = make_test_context()
        execute_tool(
            "generate_claim",
            {
                "context": "context",
                "direction": "some direction",
                "propositional_form": "ExamsAbolished → StressLow",
                "agent_id": "agent_a",
            },
            ctx,
        )
        assert len(ctx.agent_kb) == 1

    def test_invalid_propositional_form_does_not_crash(self):
        """A bad propositional form should return success=True with a warning, not crash."""
        ctx = make_test_context()
        result = execute_tool(
            "generate_claim",
            {
                "context": "context",
                "direction": "direction",
                "propositional_form": "this is not valid form at all",
                "agent_id": "agent_a",
            },
            ctx,
        )
        assert result.success is True   # does not crash
        assert result.output["kb_updated"] is False
        assert result.output["kb_warning"] is not None

    def test_missing_required_args_returns_failure(self):
        ctx = make_test_context()
        result = execute_tool("generate_claim", {}, ctx)
        assert result.success is False


    def test_context_preserved_in_output(self):
        ctx = make_test_context()
        result = execute_tool(
            "generate_claim",
            {
                "context": "my debate context",
                "direction": "argue for reduction",
                "propositional_form": "A",
                "agent_id": "agent_a",
            },
            ctx,
        )
        assert result.output["context"] == "my debate context"


class TestToolResult:
    def test_to_llm_message_success(self):
        import json
        r = ToolResult(tool_name="foo", success=True, output={"key": "val"})
        parsed = json.loads(r.to_llm_message())
        assert parsed["key"] == "val"

    def test_to_llm_message_failure(self):
        import json
        r = ToolResult(tool_name="foo", success=False, error="something broke")
        parsed = json.loads(r.to_llm_message())
        assert "error" in parsed


class TestFactGeneration:
    """Tests for fact_generation.py parser (no LLM calls)."""

    def test_parse_valid_json_response(self):
        import json
        from core.fact_generation import parse_fact_generation_response

        data = [
            {
                "text": "Abolishing exams reduces student stress.",
                "propositional": "ExamsAbolished → StressReduced",
                "relationship": "supports_proposition",
            },
            {
                "text": "Exams measure knowledge accurately.",
                "propositional": "ExamsMeasureKnowledge",
                "relationship": "contradicts_proposition",
            },
        ]
        raw = json.dumps(data)
        records = parse_fact_generation_response(raw)
        assert len(records) == 2
        assert records[0].text == "Abolishing exams reduces student stress."
        assert records[0].clause is not None

    def test_parse_markdown_fenced_response(self):
        import json
        from core.fact_generation import parse_fact_generation_response

        data = [{"text": "A fact.", "propositional": "SomeFact", "relationship": "is_independent"}]
        raw = "```json\n" + json.dumps(data) + "\n```"
        records = parse_fact_generation_response(raw)
        assert len(records) == 1

    def test_parse_invalid_json_raises(self):
        from core.fact_generation import parse_fact_generation_response
        with pytest.raises(ValueError):
            parse_fact_generation_response("not json at all {{{")

    def test_parse_skips_malformed_entries(self):
        import json
        from core.fact_generation import parse_fact_generation_response

        data = [
            {"text": "Good fact.", "propositional": "GoodAtom", "relationship": "is_independent"},
            {"bad_key": "no text or propositional"},
        ]
        records = parse_fact_generation_response(json.dumps(data))
        assert len(records) == 1

    def test_extract_fact_texts(self):
        import json
        from core.fact_generation import parse_fact_generation_response, extract_fact_texts

        data = [
            {"text": "Fact one.", "propositional": "A", "relationship": "is_independent"},
            {"text": "Fact two.", "propositional": "B", "relationship": "is_independent"},
        ]
        records = parse_fact_generation_response(json.dumps(data))
        texts = extract_fact_texts(records)
        assert texts == ["Fact one.", "Fact two."]

    def test_extract_valid_clauses_skips_none(self):
        import json
        from core.fact_generation import parse_fact_generation_response, extract_valid_clauses

        data = [
            {"text": "Valid.", "propositional": "A → B", "relationship": "is_independent"},
            {"text": "Invalid.", "propositional": "invalid with spaces not parseable at all", "relationship": "is_independent"},
        ]
        records = parse_fact_generation_response(json.dumps(data))
        clauses = extract_valid_clauses(records)
        assert len(clauses) == 1


class TestDebateLogicTools:
    """Clash detection, opponent tracking, and resolution-scored MCTS selection."""

    def test_clash_detects_conflict_with_opponent_kb(self):
        ctx = make_test_context()
        ctx.opponent_kb.tell(atom("OutcomesImprove"))
        result = execute_tool("check_contradiction", {"target": "clash", "propositional_form": "¬OutcomesImprove"}, ctx)
        assert result.success and result.output["found"] is True

    def test_clash_ignores_unrelated_clause(self):
        ctx = make_test_context()
        ctx.opponent_kb.tell(atom("OutcomesImprove"))
        result = execute_tool("check_contradiction", {"target": "clash", "propositional_form": "CostsFall"}, ctx)
        assert result.output["found"] is False

    def test_clash_requires_parseable_form(self):
        ctx = make_test_context()
        result = execute_tool("check_contradiction", {"target": "clash", "propositional_form": "not a form at all"}, ctx)
        assert result.success is False

    def test_generate_claim_records_in_opponent_track(self):
        ctx = make_test_context()
        execute_tool(
            "generate_claim",
            {"context": "c", "direction": "Outcomes improve.", "propositional_form": "OutcomesImprove", "agent_id": "agent_a"},
            ctx,
        )
        assert atom("OutcomesImprove") in ctx.opponent_kb.get_opponent_clauses()

    def test_mcts_prefers_refutation_and_avoids_self_contradiction(self):
        ctx = make_test_context()
        ctx.agent_kb.tell(atom("PilotsSucceeded"))
        ctx.opponent_kb.tell(atom("CostsRise"))
        result = execute_tool(
            "select_best_rebuttal",
            {
                "candidates": ["Pilots failed.", "Costs do not rise.", "Weather is nice."],
                "propositional_forms": ["¬PilotsSucceeded", "¬CostsRise", "WeatherNice"],
                "agent_id": "agent_a",
                "n_simulations": 30,
            },
            ctx,
        )
        out = result.output
        assert out["chosen_rebuttal"] == "Costs do not rise."
        assert out["chosen_propositional_form"] == "¬CostsRise"
        scores = {r["text"]: r["score"] for r in out["rejected_candidates"]}
        assert out["chosen_score"] > scores["Weather is nice."] > scores["Pilots failed."]

    def test_clash_against_unspoken_evidence_is_not_a_refutation(self):
        ctx = make_test_context()
        ctx.opponent_kb.tell(atom("OutcomesImprove"))  # seeded evidence, never claimed
        ctx.opponent_claimed_clauses = set()
        result = execute_tool("check_contradiction", {"target": "clash", "propositional_form": "¬OutcomesImprove"}, ctx)
        assert result.output["found"] is False

    def test_clash_against_claimed_position_is_a_refutation(self):
        ctx = make_test_context()
        ctx.opponent_kb.tell(implication_to_clause("Pilots", "OutcomesImprove"))  # evidence
        ctx.opponent_kb.tell(atom("Pilots"))                                      # claimed
        ctx.opponent_claimed_clauses = {atom("Pilots")}
        result = execute_tool("check_contradiction", {"target": "clash", "propositional_form": "¬OutcomesImprove"}, ctx)
        assert result.output["found"] is True

    def test_direct_denial_counts_even_if_evidence_agrees_with_claim(self):
        ctx = make_test_context()
        ctx.opponent_kb.tell(atom("CostHigher"))      # their evidence...
        ctx.opponent_kb.tell(atom("Ports"))
        ctx.opponent_kb.tell(implication_to_clause("Ports", "CostHigher"))
        ctx.opponent_claimed_clauses = {atom("CostHigher")}  # ...which they also claimed aloud
        result = execute_tool("check_contradiction", {"target": "clash", "propositional_form": "¬CostHigher"}, ctx)
        assert result.output["found"] is True
