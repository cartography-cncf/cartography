from cartography.intel.sysdig.transform import normalize_severity
from cartography.intel.sysdig.transform import normalize_status
from cartography.intel.sysdig.transform import transform_runtime_event_summaries
from cartography.intel.sysdig.transform import transform_vulnerabilities


def test_transform_vulnerability_rows() -> None:
    rows = [
        {
            "resource": {
                "id": "aws:arn:resource",
                "name": "prod-pod",
                "type": "KubernetesResource",
                "cluster": "prod",
                "namespace": "default",
                "imageDigest": "f" * 64,
                "imageUri": "example.com/app@sha256:" + "f" * 64,
            },
            "vulnerability": {
                "cveId": "CVE-2026-0001",
                "severity": "4",
                "status": "ACTIVE",
                "fixAvailable": True,
                "inUse": True,
                "exploitAvailable": False,
                "packageName": "Requests",
                "packageVersion": "2.31.0",
                "packageType": "pypi",
            },
            "package": {
                "name": "Requests",
                "version": "2.31.0",
                "type": "pypi",
                "purl": "pkg:pypi/Requests@2.31.0",
            },
        }
    ]

    resources, images, packages, findings = transform_vulnerabilities(rows, "tenant")

    assert resources[0]["id"] == "aws:arn:resource"
    assert images[0]["digest"] == "sha256:" + "f" * 64
    assert packages[0]["normalized_id"] == "pypi|requests|2.31.0"
    assert findings[0]["cve_id"] == "CVE-2026-0001"
    assert findings[0]["severity"] == "critical"
    assert findings[0]["status"] == "open"
    assert findings[0]["package_normalized_id"] == "pypi|requests|2.31.0"


def test_runtime_events_aggregate_by_rule_and_resource() -> None:
    rows = [
        {
            "resource": {"id": "resource-1", "name": "pod-a"},
            "event": {
                "id": "evt-1",
                "ruleName": "Terminal shell in container",
                "policyId": "policy-1",
                "severity": "high",
                "source": "syscall",
                "engine": "falco",
                "timestamp": "2026-04-25T00:00:00Z",
                "ruleTags": ["container"],
            },
        },
        {
            "resource": {"id": "resource-1", "name": "pod-a"},
            "event": {
                "id": "evt-2",
                "ruleName": "Terminal shell in container",
                "policyId": "policy-1",
                "severity": "high",
                "source": "syscall",
                "engine": "falco",
                "timestamp": "2026-04-25T01:00:00Z",
                "ruleTags": ["container"],
            },
        },
    ]

    resources, summaries = transform_runtime_event_summaries(rows, "tenant")

    assert len(resources) == 1
    assert len(summaries) == 1
    assert summaries[0]["event_count"] == 2
    assert summaries[0]["first_seen"] == "2026-04-25T00:00:00Z"
    assert summaries[0]["last_seen"] == "2026-04-25T01:00:00Z"
    assert summaries[0]["rule_tags"] == ["container"]


def test_normalization_helpers() -> None:
    assert normalize_severity("1") == "low"
    assert normalize_severity("CRITICAL") == "critical"
    assert normalize_status("risk accepted") == "accepted"
    assert normalize_status("ACTIVE") == "open"
