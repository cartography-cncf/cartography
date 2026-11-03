"""
Unit tests for Semgrep findings helpers.
"""

import copy
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from requests.exceptions import HTTPError

from cartography.intel.semgrep import findings as semgrep_findings
from cartography.intel.semgrep.findings import transform_ai_sast_findings
from cartography.intel.semgrep.findings import transform_sca_vulns
from tests.data.semgrep.aisast import AI_SAST_FINDING_ID
from tests.data.semgrep.aisast import AI_SAST_RESPONSE
from tests.data.semgrep.aisast import RAW_FINDINGS
from tests.data.semgrep.sca import SCA_RESPONSE


def _response(findings=None, status_code=200):
    response = MagicMock(status_code=status_code)
    response.json.return_value = {"findings": findings or []}
    if status_code >= 400:
        response.raise_for_status.side_effect = HTTPError(response=response)
    return response


@pytest.mark.parametrize(
    "getter, issue_type",
    [
        (semgrep_findings.get_sast_findings, "sast"),
        (semgrep_findings.get_sca_vulns, "sca"),
        (semgrep_findings.get_ai_sast_findings, "ai_sast"),
    ],
)
@patch("cartography.intel.semgrep.findings.requests.get")
def test_get_findings_requests_issue_type_and_pages(mock_get, getter, issue_type):
    # Arrange
    mock_get.side_effect = [
        _response(RAW_FINDINGS),
        _response(RAW_FINDINGS),
        _response([]),
    ]

    # Act
    pages = getter("token", "my-deployment")
    first_page = next(pages)

    # Assert: each page is yielded before the next one is requested
    assert first_page == RAW_FINDINGS
    assert mock_get.call_count == 1
    assert list(pages) == [RAW_FINDINGS]
    calls = mock_get.call_args_list
    assert calls[0].args[0] == (
        "https://semgrep.dev/api/v1/deployments/my-deployment/findings"
    )
    assert [c.kwargs["params"]["page"] for c in calls] == [0, 1, 2]
    assert {c.kwargs["params"]["issue_type"] for c in calls} == {issue_type}
    assert {c.kwargs["params"]["ref"] for c in calls} == {"_default"}


@patch("cartography.intel.semgrep.findings.requests.get")
def test_get_findings_does_not_retry_client_errors(mock_get):
    # Arrange
    mock_get.return_value = _response(status_code=403)

    # Act and assert
    with pytest.raises(HTTPError):
        list(semgrep_findings.get_ai_sast_findings("token", "my-deployment"))
    assert mock_get.call_count == 1


@patch("cartography.intel.semgrep.findings.requests.get")
def test_get_findings_retries_server_errors_then_raises(mock_get):
    # Arrange
    mock_get.return_value = _response(status_code=500)

    # Act and assert
    with pytest.raises(HTTPError):
        list(semgrep_findings.get_ai_sast_findings("token", "my-deployment"))
    assert mock_get.call_count == semgrep_findings._MAX_RETRIES


@patch("cartography.intel.semgrep.findings.requests.get")
def test_get_findings_retries_rate_limit_then_succeeds(mock_get):
    # Arrange
    mock_get.side_effect = [
        _response(status_code=429),
        _response(RAW_FINDINGS),
        _response([]),
    ]

    # Act
    result = list(semgrep_findings.get_ai_sast_findings("token", "my-deployment"))

    # Assert
    assert result == [RAW_FINDINGS]
    assert [c.kwargs["params"]["page"] for c in mock_get.call_args_list] == [0, 0, 1]


def test_transform_sca_vulns_uppercases_reachability():
    raw_vulns = copy.deepcopy(SCA_RESPONSE["findings"])

    vulns, _ = transform_sca_vulns(raw_vulns)

    assert vulns[0]["reachability"] == "REACHABLE"
    assert vulns[1]["reachability"] == "UNREACHABLE"


def test_transform_sca_vulns_handles_null_reachability():
    # Semgrep only runs reachability analysis for supported ecosystems/rules, so
    # `reachability` comes back as null otherwise. transform_sca_vulns must not
    # crash on it (regression test for AttributeError on None.upper()).
    raw_vulns = copy.deepcopy(SCA_RESPONSE["findings"])
    raw_vulns[0]["reachability"] = None

    vulns, _ = transform_sca_vulns(raw_vulns)

    assert vulns[0]["reachability"] is None


def test_transform_ai_sast_findings():
    # Arrange
    raw_findings = copy.deepcopy(AI_SAST_RESPONSE["findings"])

    # Act
    findings = transform_ai_sast_findings(raw_findings)

    # Assert
    assert len(findings) == 1
    finding = findings[0]
    assert finding["id"] == AI_SAST_FINDING_ID
    assert finding["repositoryName"] == "simpsoncorp/sample_repo"
    assert finding["repositoryUrl"] == "https://github.com/simpsoncorp/sample_repo"
    assert finding["branch"] == "main"
    assert finding["ruleId"] == "ai.detection.idor"
    assert finding["title"] == "ai.detection.idor"
    # rule.message wins over the deprecated top-level rule_message
    assert finding["description"].startswith("Insecure direct object reference")
    assert finding["severity"] == "HIGH"
    assert finding["confidence"] == "MEDIUM"
    assert finding["categories"] == ["security"]
    assert finding["vulnerabilityClasses"] == [
        "Insecure Direct Object Reference (IDOR)"
    ]
    assert finding["filePath"] == "src/api/orders.py"
    assert (
        finding["startLine"],
        finding["startCol"],
        finding["endLine"],
        finding["endCol"],
    ) == (17, 5, 19, 30)
    assert finding["fixStatus"] == "open"
    assert finding["triageStatus"] == "untriaged"
    assert finding["assistantId"] == f"semgrep-assistant-{AI_SAST_FINDING_ID}"


def test_transform_ai_sast_findings_handles_missing_optional_fields():
    # Arrange: optional fields can be absent or null; transform must not raise.
    raw_findings = [
        {
            "id": 1,
            "repository": {"name": "org/repo", "url": "https://github.com/org/repo"},
            "rule_name": "ai.detection.legacy",
            "rule_message": "legacy message",
            "severity": None,
            "confidence": None,
            "location": None,
        }
    ]

    # Act
    findings = transform_ai_sast_findings(raw_findings)

    # Assert
    finding = findings[0]
    # Falls back to the deprecated rule_name / rule_message fields
    assert finding["ruleId"] == "ai.detection.legacy"
    assert finding["description"] == "legacy message"
    assert finding["severity"] is None
    assert finding["confidence"] is None
    assert finding["categories"] == []
    assert finding["cweNames"] == []
    assert finding["filePath"] is None
    assert finding["startLine"] is None
