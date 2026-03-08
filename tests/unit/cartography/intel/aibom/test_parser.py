import json
from typing import Any

import pytest

from cartography.intel.aibom.parser import parse_aibom_document
from tests.data.aibom.aibom_sample import AIBOM_REPORT


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

    assert agent.metadata_json == json.dumps(
        {"approval": "human", "mcp": True},
        sort_keys=True,
    )
    assert tool.metadata_json == json.dumps(
        {"approval": "required", "transport": "mcp"},
        sort_keys=True,
    )
    assert model.model_name == "gpt-4.1-mini"
    assert {
        relationship.relationship_type for relationship in source.relationships
    } == {
        "USES_LLM",
        "USES_MEMORY",
        "USES_PROMPT",
        "USES_TOOL",
    }


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
