"""
test_tool_schemas.py — Unit tests for tool_schemas.py
Phase 4: verify schema structure, completeness, and the as_openai_tools() wrapper.
No LLM calls — these are pure structural/contract tests.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from tools.tool_schemas import (
    TOOL_SCHEMAS,
    TOOL_SCHEMA_BY_NAME,
    RETRIEVE_RELEVANT_FACT_SCHEMA,
    CHECK_CONTRADICTION_SCHEMA,
    SELECT_BEST_REBUTTAL_SCHEMA,
    GENERATE_CLAIM_SCHEMA,
    as_openai_tools,
)


EXPECTED_TOOL_NAMES = {
    "retrieve_relevant_fact",
    "check_contradiction",
    "select_best_rebuttal",
    "generate_claim",
}


class TestToolSchemasList:
    def test_four_tools_defined(self):
        assert len(TOOL_SCHEMAS) == 4

    def test_all_expected_tools_present(self):
        names = {s["name"] for s in TOOL_SCHEMAS}
        assert names == EXPECTED_TOOL_NAMES

    def test_schema_by_name_covers_all_tools(self):
        assert set(TOOL_SCHEMA_BY_NAME.keys()) == EXPECTED_TOOL_NAMES

    def test_schema_by_name_matches_list(self):
        for schema in TOOL_SCHEMAS:
            assert TOOL_SCHEMA_BY_NAME[schema["name"]] is schema


class TestSchemaStructure:
    @pytest.mark.parametrize("schema", TOOL_SCHEMAS, ids=lambda s: s["name"])
    def test_has_name(self, schema):
        assert "name" in schema
        assert isinstance(schema["name"], str)
        assert len(schema["name"]) > 0

    @pytest.mark.parametrize("schema", TOOL_SCHEMAS, ids=lambda s: s["name"])
    def test_has_description(self, schema):
        assert "description" in schema
        assert isinstance(schema["description"], str)
        assert len(schema["description"]) > 20   # must be meaningful, not a placeholder

    @pytest.mark.parametrize("schema", TOOL_SCHEMAS, ids=lambda s: s["name"])
    def test_has_parameters(self, schema):
        assert "parameters" in schema
        params = schema["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

    @pytest.mark.parametrize("schema", TOOL_SCHEMAS, ids=lambda s: s["name"])
    def test_required_params_exist_in_properties(self, schema):
        params = schema["parameters"]
        for req in params["required"]:
            assert req in params["properties"], (
                f"Required param '{req}' not in properties of '{schema['name']}'"
            )

    @pytest.mark.parametrize("schema", TOOL_SCHEMAS, ids=lambda s: s["name"])
    def test_each_property_has_type_and_description(self, schema):
        for prop_name, prop_def in schema["parameters"]["properties"].items():
            assert "type" in prop_def or "enum" in prop_def, (
                f"Property '{prop_name}' in '{schema['name']}' must have 'type' or 'enum'"
            )
            assert "description" in prop_def, (
                f"Property '{prop_name}' in '{schema['name']}' must have 'description'"
            )


class TestSpecificSchemaContracts:
    def test_retrieve_required_claim_topic(self):
        assert "claim_topic" in RETRIEVE_RELEVANT_FACT_SCHEMA["parameters"]["required"]

    def test_check_contradiction_required_target_and_agent_id(self):
        required = CHECK_CONTRADICTION_SCHEMA["parameters"]["required"]
        assert "target" in required
        assert "agent_id" in required

    def test_check_contradiction_target_has_enum(self):
        target_prop = CHECK_CONTRADICTION_SCHEMA["parameters"]["properties"]["target"]
        assert "enum" in target_prop
        assert set(target_prop["enum"]) == {"self", "opponent", "combined"}

    def test_select_best_rebuttal_required_candidates(self):
        assert "candidates" in SELECT_BEST_REBUTTAL_SCHEMA["parameters"]["required"]

    def test_select_best_rebuttal_candidates_is_array(self):
        prop = SELECT_BEST_REBUTTAL_SCHEMA["parameters"]["properties"]["candidates"]
        assert prop["type"] == "array"
        assert "items" in prop

    def test_generate_claim_required_fields(self):
        required = set(GENERATE_CLAIM_SCHEMA["parameters"]["required"])
        assert "context" in required
        assert "direction" in required
        assert "propositional_form" in required
        assert "agent_id" in required


class TestAsOpenAITools:
    def test_wraps_each_schema(self):
        wrapped = as_openai_tools()
        assert len(wrapped) == len(TOOL_SCHEMAS)

    def test_each_has_type_function(self):
        for item in as_openai_tools():
            assert item["type"] == "function"
            assert "function" in item

    def test_function_field_is_original_schema(self):
        wrapped = as_openai_tools()
        for i, item in enumerate(wrapped):
            assert item["function"] is TOOL_SCHEMAS[i]

    def test_custom_schema_list(self):
        custom = as_openai_tools([RETRIEVE_RELEVANT_FACT_SCHEMA])
        assert len(custom) == 1
        assert custom[0]["function"]["name"] == "retrieve_relevant_fact"
