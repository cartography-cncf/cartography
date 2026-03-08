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
        assert str(exc) == "AIBOM document has invalid report format"


def test_parse_aibom_document_rejects_invalid_source_payload() -> None:
    document: dict[str, Any] = {
        "aibom_analysis": {
            "sources": {
                "000000000000.dkr.ecr.us-east-1.amazonaws.com/example:v1": [],
            },
        },
    }

    try:
        parse_aibom_document(document)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc) == "AIBOM document has invalid source payload format"
