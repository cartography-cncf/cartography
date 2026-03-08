from typing import Any

from cartography.intel.aibom.parser import parse_aibom_document


def test_parse_aibom_document_rejects_invalid_report_wrapper() -> None:
    document: dict[str, Any] = {
        "image_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/example:v1",
        "report": [],
    }

    try:
        parse_aibom_document(document)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "aibom_analysis" in str(exc)


def test_parse_aibom_document_rejects_invalid_source_payload() -> None:
    """A non-dict source payload is silently skipped, returning no sources."""
    document: dict[str, Any] = {
        "aibom_analysis": {
            "sources": {
                "000000000000.dkr.ecr.us-east-1.amazonaws.com/example:v1": [],
            },
        },
    }

    result = parse_aibom_document(document)
    assert result == []
