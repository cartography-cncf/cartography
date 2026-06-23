from cartography.intel.wiz.issues import transform as transform_issues
from cartography.intel.wiz.resources import transform as transform_resources
from cartography.intel.wiz.vulnerabilities import get_finding_id
from cartography.intel.wiz.vulnerabilities import transform as transform_vulnerabilities
from tests.data.wiz import CVE_ID_1
from tests.data.wiz import ISSUES
from tests.data.wiz import RESOURCE_ID_1
from tests.data.wiz import RESOURCES
from tests.data.wiz import TENANT_ID
from tests.data.wiz import VULNERABILITY_FINDINGS
from tests.data.wiz import VULNERABILITY_WITHOUT_ID


def test_transform_resources_flattens_project_and_tag_metadata():
    resources = transform_resources(RESOURCES[:1])

    assert resources == [
        {
            "id": RESOURCE_ID_1,
            "name": "prod-instance",
            "external_id": "arn:aws:ec2:us-east-1:123456789012:instance/i-123",
            "resource_type": "VIRTUAL_MACHINE",
            "cloud_platform": "AWS",
            "cloud_provider_url": None,
            "status": "ACTIVE",
            "region": "us-east-1",
            "cloud_account_id": "cloud-account-1",
            "cloud_account_name": "prod-aws",
            "cloud_account_provider": "AWS",
            "cloud_account_external_id": "123456789012",
            "project_ids": ["project-1"],
            "project_names": ["Production"],
            "tags": ["env=prod"],
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-02T00:00:00Z",
            "is_open_to_all_internet": False,
            "is_accessible_from_internet": True,
            "has_access_to_sensitive_data": True,
            "has_admin_privileges": False,
            "has_high_privileges": True,
            "has_sensitive_data": True,
        },
    ]


def test_transform_issues_extracts_resource_and_project_metadata():
    issues = transform_issues(ISSUES)

    assert issues[0]["id"] == "wiz-issue-1"
    assert issues[0]["name"] == "Public VM"
    assert issues[0]["resource_id"] == RESOURCE_ID_1
    assert issues[0]["project_ids"] == ["project-1"]
    assert issues[0]["service_ticket_urls"] == ["https://ticket/SEC-1"]


def test_transform_vulnerabilities_extracts_cve_and_resource_metadata():
    findings = transform_vulnerabilities(VULNERABILITY_FINDINGS, TENANT_ID)

    assert findings[0]["id"] == "wiz-vuln-1"
    assert findings[0]["cve_id"] == CVE_ID_1
    assert findings[0]["resource_id"] == RESOURCE_ID_1
    assert findings[0]["resource_external_id"] == (
        "arn:aws:ec2:us-east-1:123456789012:instance/i-123"
    )


def test_get_finding_id_falls_back_to_deterministic_composite_id():
    assert get_finding_id(VULNERABILITY_WITHOUT_ID, TENANT_ID) == (
        f"WizVulnerabilityFinding|{TENANT_ID}|{RESOURCE_ID_1}|{CVE_ID_1}|1.0.0"
    )
