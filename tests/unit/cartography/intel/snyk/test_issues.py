from cartography.intel.snyk.issues import transform
from tests.data.snyk.data import ISSUE_ADVISORY_ID
from tests.data.snyk.data import ISSUE_CVE_ID
from tests.data.snyk.data import ISSUES
from tests.data.snyk.data import ORG_ID
from tests.data.snyk.data import PROJECT_ID


def test_transform_issues_extracts_cves_and_conditional_label_flags():
    result = transform(ISSUES, ORG_ID)

    by_id = {item["id"]: item for item in result}
    assert by_id[ISSUE_CVE_ID]["cve_id"] == "CVE-2021-44906"
    assert by_id[ISSUE_CVE_ID]["has_cve"] == "true"
    assert by_id[ISSUE_CVE_ID]["project_id"] == PROJECT_ID
    assert by_id[ISSUE_CVE_ID]["identifiers"] == ["CVE-2021-44906", "CWE-1321"]
    assert by_id[ISSUE_ADVISORY_ID]["cve_id"] is None
    assert by_id[ISSUE_ADVISORY_ID]["has_cve"] == "false"


def test_transform_issues_preserves_status_when_ignored():
    issue = {
        "id": "ignored-resolved",
        "type": "issue",
        "attributes": {
            "title": "Ignored resolved issue",
            "status": "resolved",
            "ignored": True,
        },
    }

    result = transform([issue], ORG_ID)

    assert result[0]["status"] == "resolved"
    assert result[0]["ignored"] is True
