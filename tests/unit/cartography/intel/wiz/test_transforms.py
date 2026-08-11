from cartography.intel.wiz.findings import get_finding_id
from cartography.intel.wiz.findings import transform as transform_findings
from cartography.intel.wiz.issues import transform as transform_issues
from cartography.intel.wiz.util import filter_by_project_ids
from tests.data.wiz import CONFIGURATION_FINDING_ID_1
from tests.data.wiz import CONFIGURATION_FINDINGS
from tests.data.wiz import CVE_ID_1
from tests.data.wiz import DETECTION_ID_1
from tests.data.wiz import DETECTIONS
from tests.data.wiz import FINDINGS
from tests.data.wiz import ISSUES
from tests.data.wiz import RESOURCE_ID_1
from tests.data.wiz import TENANT_ID
from tests.data.wiz import VULNERABILITY_FINDINGS
from tests.data.wiz import VULNERABILITY_WITHOUT_ID


def test_transform_issues_extracts_resource_and_project_metadata():
    issues = transform_issues(ISSUES)

    assert issues[0]["id"] == "wiz-issue-1"
    assert issues[0]["name"] == "Public VM"
    assert issues[0]["resource_id"] == RESOURCE_ID_1
    assert issues[0]["project_ids"] == ["project-1"]
    assert issues[0]["service_ticket_urls"] == ["https://ticket/SEC-1"]


def test_transform_findings_extracts_vulnerability_cve_and_resource_metadata():
    findings = transform_findings(VULNERABILITY_FINDINGS, TENANT_ID)

    assert findings[0]["id"] == "wiz-vuln-1"
    assert findings[0]["finding_type"] == "VULNERABILITY"
    assert findings[0]["cve_id"] == CVE_ID_1
    assert findings[0]["resource_id"] == RESOURCE_ID_1
    assert findings[0]["resource_external_id"] == (
        "arn:aws:ec2:us-east-1:123456789012:instance/i-123"
    )


def test_transform_findings_extracts_configuration_metadata():
    findings = transform_findings(CONFIGURATION_FINDINGS, TENANT_ID)

    assert findings[0]["id"] == CONFIGURATION_FINDING_ID_1
    assert findings[0]["finding_type"] == "CONFIGURATION"
    assert findings[0]["result"] == "FAIL"
    assert findings[0]["updated_at"] == "2026-01-07T00:05:00Z"
    assert findings[0]["rule_id"] == "config-rule-1"
    assert findings[0]["resource_external_id"] == "arn:aws:s3:::public-bucket"
    assert findings[0]["project_ids"] == ["project-1"]


def test_transform_findings_extracts_detection_metadata():
    findings = transform_findings(DETECTIONS, TENANT_ID)

    assert findings[0]["id"] == DETECTION_ID_1
    assert findings[0]["finding_type"] == "DETECTION"
    assert findings[0]["rule_id"] == "detect-rule-1"
    assert findings[0]["actor_ids"] == ["actor-1"]
    assert findings[0]["cloud_account_ids"] == ["cloud-account-1"]
    assert findings[0]["triggering_event_ids"] == ["event-1"]


def test_transform_findings_does_not_link_detection_description_cves():
    detection = {
        **DETECTIONS[0],
        "description": "Suspicious process mentioned CVE-2024-12345",
    }

    findings = transform_findings([detection], TENANT_ID)

    assert findings[0]["cve_id"] is None


def test_transform_findings_preserves_all_supported_finding_types():
    findings = transform_findings(FINDINGS, TENANT_ID)

    assert {finding["finding_type"] for finding in findings} == {
        "CONFIGURATION",
        "DETECTION",
        "VULNERABILITY",
    }


def test_get_finding_id_falls_back_to_deterministic_composite_id():
    assert get_finding_id(VULNERABILITY_WITHOUT_ID, TENANT_ID) == (
        f"WizFinding|VULNERABILITY|{TENANT_ID}|{RESOURCE_ID_1}|{CVE_ID_1}|1.0.0"
    )


def test_get_finding_id_ignores_mutable_timestamps():
    finding = {
        "_wiz_finding_type": "CONFIGURATION",
        "resource": {"id": RESOURCE_ID_1},
        "rule": {"id": "rule-1"},
        "updatedAt": "2026-01-01T00:00:00Z",
        "firstSeenAt": "2026-01-01T00:00:00Z",
    }
    updated_finding = {
        **finding,
        "updatedAt": "2026-01-02T00:00:00Z",
        "firstSeenAt": "2026-01-02T00:00:00Z",
    }

    assert get_finding_id(finding, TENANT_ID) == get_finding_id(
        updated_finding,
        TENANT_ID,
    )


def test_filter_by_project_ids_filters_records_with_project_metadata():
    records = [
        {"id": "kept", "projects": [{"id": "project-1"}]},
        {"id": "dropped", "projects": [{"id": "project-2"}]},
    ]

    assert filter_by_project_ids(records, ["project-1"]) == [records[0]]


def test_filter_by_project_ids_keeps_records_without_project_metadata():
    records = [
        {"id": "kept-with-project", "projects": [{"id": "project-1"}]},
        {"id": "kept-without-project"},
    ]

    assert filter_by_project_ids(records, ["project-1"]) == records
