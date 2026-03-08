from typing import Any

import pytest

from cartography.intel.aibom.parser import parse_aibom_document


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


def test_parse_aibom_document_skips_invalid_source_payload() -> None:
    """A non-dict source payload is silently skipped, returning no sources."""
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
    assert result == []
