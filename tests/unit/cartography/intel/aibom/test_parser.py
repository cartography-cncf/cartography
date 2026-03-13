import copy
from typing import Any
from typing import cast

import pytest

from cartography.intel.aibom.parser import parse_aibom_document
from tests.data.aibom.aibom_sample import AIBOM_REPORT
from tests.data.aibom.aibom_sample import TEST_SOURCE_KEY


def test_parse_aibom_document_rejects_missing_image_uri() -> None:
    document: dict[str, Any] = {
        "report": {
            "aibom_analysis": {
                "sources": {},
            },
        },
    }

    with pytest.raises(ValueError, match="image_uri"):
        parse_aibom_document(document)


def test_parse_aibom_document_rejects_missing_report() -> None:
    document: dict[str, Any] = {
        "image_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/example:v1",
    }

    with pytest.raises(ValueError, match="report"):
        parse_aibom_document(document)


def test_parse_aibom_document_rejects_invalid_report_wrapper() -> None:
    document: dict[str, Any] = {
        "image_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/example:v1",
        "report": [],
    }

    with pytest.raises(ValueError, match="report"):
        parse_aibom_document(document)


def test_parse_aibom_document_parses_rich_document() -> None:
    document = parse_aibom_document(AIBOM_REPORT, report_location="/tmp/aibom.json")

    assert document.image_uri.endswith("multi-arch-repository:v1.0")
    assert document.report_location == "/tmp/aibom.json"
    assert document.total_sources == 1
    assert document.total_components == 6
    assert document.total_workflows == 2
    assert document.total_relationships == 4

    source = document.sources[0]
    assert source.source_kind == "container_image"
    assert source.total_components == 6
    assert source.total_workflows == 2
    assert source.total_relationships == 4

    agent = next(
        component for component in source.components if component.category == "agent"
    )
    tool = next(
        component for component in source.components if component.category == "tool"
    )
    model = next(
        component for component in source.components if component.category == "model"
    )

    assert agent.framework == "pydantic_ai"
    assert agent.label == "customer_assistant"
    assert tool.framework == "internal_mcp"
    assert tool.label == "customer_lookup_tool"
    assert model.model_name == "gpt-4.1-mini"
    assert {
        relationship.relationship_type for relationship in source.relationships
    } == {
        "USES_LLM",
        "USES_MEMORY",
        "USES_PROMPT",
        "USES_TOOL",
    }


def test_parse_aibom_document_parses_flat_from_to_relationships() -> None:
    report = cast(dict[str, Any], copy.deepcopy(AIBOM_REPORT))
    source = cast(
        dict[str, Any],
        report["report"]["aibom_analysis"]["sources"][TEST_SOURCE_KEY],
    )
    relationships = cast(list[dict[str, Any]], source["relationships"])
    relationship = relationships[0]
    relationship.pop("source")
    relationship.pop("target")
    relationship.update(
        {
            "from_instance_id": "agent_main",
            "from_name": "pydantic_ai.Agent",
            "from_category": "agent",
            "to_instance_id": "model_primary",
            "to_name": "openai:gpt-4.1-mini",
            "to_category": "model",
        },
    )

    document = parse_aibom_document(report)

    parsed_relationship = document.sources[0].relationships[0]
    assert parsed_relationship.source_instance_id == "agent_main"
    assert parsed_relationship.source_name == "pydantic_ai.Agent"
    assert parsed_relationship.source_category == "agent"
    assert parsed_relationship.target_instance_id == "model_primary"
    assert parsed_relationship.target_name == "openai:gpt-4.1-mini"
    assert parsed_relationship.target_category == "model"


def test_parse_aibom_document_parses_flat_source_target_relationships() -> None:
    report = cast(dict[str, Any], copy.deepcopy(AIBOM_REPORT))
    source = cast(
        dict[str, Any],
        report["report"]["aibom_analysis"]["sources"][TEST_SOURCE_KEY],
    )
    relationships = cast(list[dict[str, Any]], source["relationships"])
    relationship = relationships[0]
    relationship.pop("source")
    relationship.pop("target")
    relationship.update(
        {
            "source_instance_id": "agent_main",
            "source_name": "pydantic_ai.Agent",
            "source_category": "agent",
            "target_instance_id": "model_primary",
            "target_name": "openai:gpt-4.1-mini",
            "target_category": "model",
        },
    )

    document = parse_aibom_document(report)

    parsed_relationship = document.sources[0].relationships[0]
    assert parsed_relationship.source_instance_id == "agent_main"
    assert parsed_relationship.source_name == "pydantic_ai.Agent"
    assert parsed_relationship.source_category == "agent"
    assert parsed_relationship.target_instance_id == "model_primary"
    assert parsed_relationship.target_name == "openai:gpt-4.1-mini"
    assert parsed_relationship.target_category == "model"


def test_parse_aibom_document_merges_partial_source_target_and_from_to_fields() -> None:
    report = cast(dict[str, Any], copy.deepcopy(AIBOM_REPORT))
    source = cast(
        dict[str, Any],
        report["report"]["aibom_analysis"]["sources"][TEST_SOURCE_KEY],
    )
    relationships = cast(list[dict[str, Any]], source["relationships"])
    relationship = relationships[0]
    relationship.pop("source")
    relationship.pop("target")
    relationship.update(
        {
            "source_name": "pydantic_ai.Agent",
            "source_category": "agent",
            "from_instance_id": "agent_main",
            "target_name": "openai:gpt-4.1-mini",
            "target_category": "model",
            "to_instance_id": "model_primary",
        },
    )

    document = parse_aibom_document(report)

    parsed_relationship = document.sources[0].relationships[0]
    assert parsed_relationship.source_instance_id == "agent_main"
    assert parsed_relationship.source_name == "pydantic_ai.Agent"
    assert parsed_relationship.source_category == "agent"
    assert parsed_relationship.target_instance_id == "model_primary"
    assert parsed_relationship.target_name == "openai:gpt-4.1-mini"
    assert parsed_relationship.target_category == "model"


def test_parse_aibom_document_skips_invalid_source_payload() -> None:
    document: dict[str, Any] = {
        "image_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/example:v1",
        "report": {
            "aibom_analysis": {
                "sources": {
                    "/tmp/app": [],
                },
            },
        },
    }

    result = parse_aibom_document(document)
    assert result.sources == []
