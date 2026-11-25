from copy import deepcopy

import pytest

from cartography.intel.sweet import attack_chains
from cartography.intel.sweet import vulnerabilities
from cartography.intel.sweet.finding_sets import transform_content
from cartography.intel.sweet.finding_sets import WorkloadFindingSets
from tests.data.sweet import CVE_VULNERABILITY_ID
from tests.data.sweet import SECOND_API_VULNERABILITY_ID
from tests.data.sweet import TENANT_ID
from tests.data.sweet import VULNERABILITIES


@pytest.mark.parametrize(
    "raw_id, vulnerability_id, cve_id, has_cve",
    [
        ("cve-2024-3094", "CVE-2024-3094", "CVE-2024-3094", "true"),
        ("GHSA-xxxx-yyyy-zzzz", "GHSA-xxxx-yyyy-zzzz", None, "false"),
    ],
)
def test_vulnerability_ids_uppercase_cves_and_leave_other_ids(
    raw_id,
    vulnerability_id,
    cve_id,
    has_cve,
):
    # Act
    result = vulnerabilities.transform_vulnerability(
        {"id": "v1", "cve": raw_id},
        TENANT_ID,
    )

    # Assert
    assert result["id"] == f"{TENANT_ID}:{vulnerability_id}"
    assert result["vulnerability_id"] == vulnerability_id
    assert result["cve_id"] == cve_id
    assert result["has_cve"] == has_cve


@pytest.mark.parametrize(
    "digest, affected_image_digest",
    [
        ("B" * 64, "sha256:" + "b" * 64),
        ("sha512:abc", None),
    ],
)
def test_content_image_digest_is_matched_only_as_sha256(digest, affected_image_digest):
    # Act
    result = transform_content({"id": "v1", "image": {"digest": digest}}, TENANT_ID)

    # Assert
    assert result["image_digest"] == digest
    assert result["affected_image_digest"] == affected_image_digest


def test_content_without_id_image_or_package_has_null_fields():
    # Act
    result = transform_content(
        {"id": "v1", "image": None, "package": None, "codeOwner": None},
        TENANT_ID,
    )

    # Assert
    assert result["image_name"] is None
    assert result["affected_image_digest"] is None
    assert result["package_name"] is None
    assert result["code_owner_email"] is None
    assert result["sweet_vulnerability_id"] is None


def test_content_is_shared_by_workloads_but_not_by_tenants():
    # Arrange
    first, _, second = VULNERABILITIES

    # Act
    first_content = transform_content(first, TENANT_ID)
    second_content = transform_content(second, TENANT_ID)
    other_tenant_content = transform_content(first, "other-tenant")

    # Assert
    assert first_content["id"] == second_content["id"]
    assert other_tenant_content["id"] != first_content["id"]


def test_workloads_with_the_same_findings_share_a_set():
    # Arrange
    finding_sets = WorkloadFindingSets(TENANT_ID)
    for raw in VULNERABILITIES:
        finding_sets.add(raw, transform_content(raw, TENANT_ID)["id"])

    # Act
    sets, slots, workloads = finding_sets.build()

    # Assert
    by_workload = {w["workload"]: w for w in workloads}
    assert len(sets) == 2
    assert (
        by_workload["api"]["finding_set_id"] == by_workload["api-2"]["finding_set_id"]
    )
    assert by_workload["api"]["finding_ids"] == [CVE_VULNERABILITY_ID]
    assert by_workload["api-2"]["finding_ids"] == [SECOND_API_VULNERABILITY_ID]
    assert by_workload["api"]["last_executed_ms"] == [0]
    assert by_workload["api-2"]["last_executed_ms"] == [1794718800000]
    assert {(s["setid"], tuple(s["slots"])) for s in slots} == {
        (by_workload["api"]["finding_set_id"], (0,)),
        (by_workload["worker"]["finding_set_id"], (0,)),
    }


def test_detection_returned_twice_keeps_its_latest_version():
    # Arrange
    earlier = deepcopy(VULNERABILITIES[0])
    later = {**earlier, "lastDetected": "2026-11-16T00:00:00Z", "status": "Ignored"}
    finding_sets = WorkloadFindingSets(TENANT_ID)
    later_content_id = transform_content(later, TENANT_ID)["id"]

    # Act
    finding_sets.add(earlier, transform_content(earlier, TENANT_ID)["id"])
    finding_sets.add(later, later_content_id)
    sets, _, workloads = finding_sets.build()

    # Assert
    assert [s["content_ids"] for s in sets] == [[later_content_id]]
    assert workloads[0]["last_detected_ms"] == [1794787200000]


def test_attack_chain_domain_is_normalized_like_dns_record_names():
    # Arrange
    raw = [{"id": "c1", "domain": " API.Example.com.:8443 "}]

    # Act
    result = attack_chains.transform(raw)

    # Assert
    assert result[0]["domain"] == "api.example.com"


def test_attack_chain_ipv6_domain_keeps_its_colons():
    # Arrange
    raw = [{"id": "c1", "domain": "2001:db8::1"}]

    # Act
    result = attack_chains.transform(raw)

    # Assert
    assert result[0]["domain"] == "2001:db8::1"


def test_attack_chain_endpoints_are_formatted_as_method_and_path():
    # Arrange
    raw = [
        {
            "id": "c1",
            "endpoints": [
                {"method": "GET", "path": "/v1/orders/{id}"},
                {"method": "", "path": "/health"},
                {},
            ],
        },
    ]

    # Act
    result = attack_chains.transform(raw)

    # Assert
    assert result[0]["endpoints"] == ["GET /v1/orders/{id}", "/health"]


def test_attack_chain_empty_strings_become_null():
    # Arrange
    raw = [
        {"id": "c1", "confidence": "", "executionName": "", "campaignName": ""},
    ]

    # Act
    result = attack_chains.transform(raw)

    # Assert
    assert result[0]["confidence"] is None
    assert result[0]["execution_name"] is None
    assert result[0]["campaign_name"] is None


def test_content_status_is_normalized_from_sweet_title_case():
    # Arrange
    raw = [
        {"id": "1", "cve": "CVE-2026-0001", "status": "Open"},
        {"id": "2", "cve": "CVE-2026-0002", "status": "In Progress"},
        {"id": "3", "cve": "CVE-2026-0003", "status": "Ignored"},
        {"id": "4", "cve": "CVE-2026-0004", "status": None},
    ]

    # Act
    result = [transform_content(v, TENANT_ID) for v in raw]

    # Assert
    assert [v["status"] for v in result] == ["open", "in_progress", "ignored", None]


def test_vulnerability_status_filter_uses_sweet_title_case(mocker):
    # Arrange
    iter_pages = mocker.patch(
        "cartography.intel.sweet.api.iter_pages",
        return_value=[],
    )

    # Act
    vulnerabilities.get(mocker.MagicMock(), "https://eapi.sweet.security")

    # Assert
    assert iter_pages.call_args.args[3] == {"status": "Open,In Progress,Ignored"}
