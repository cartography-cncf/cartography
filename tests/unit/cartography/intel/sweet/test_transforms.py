from cartography.intel.sweet import attack_chains
from cartography.intel.sweet import vulnerabilities


def test_vulnerability_with_lowercase_cve_id_is_normalized():
    # Arrange
    raw = [{"id": "v1", "cve": "cve-2024-3094"}]

    # Act
    result = vulnerabilities.transform(raw)

    # Assert
    assert result[0]["vulnerability_id"] == "cve-2024-3094"
    assert result[0]["cve_id"] == "CVE-2024-3094"
    assert result[0]["has_cve"] == "true"


def test_vulnerability_with_non_cve_id_has_no_cve():
    # Arrange
    raw = [{"id": "v1", "cve": "GHSA-xxxx-yyyy-zzzz"}]

    # Act
    result = vulnerabilities.transform(raw)

    # Assert
    assert result[0]["vulnerability_id"] == "GHSA-xxxx-yyyy-zzzz"
    assert result[0]["cve_id"] is None
    assert result[0]["has_cve"] == "false"


def test_vulnerability_bare_image_digest_is_prefixed_for_matching():
    # Arrange
    raw = [{"id": "v1", "image": {"digest": "B" * 64}}]

    # Act
    result = vulnerabilities.transform(raw)

    # Assert
    assert result[0]["image_digest"] == "B" * 64
    assert result[0]["affected_image_digest"] == "sha256:" + "b" * 64


def test_vulnerability_non_sha256_image_digest_is_not_matched():
    # Arrange
    raw = [{"id": "v1", "image": {"digest": "sha512:abc"}}]

    # Act
    result = vulnerabilities.transform(raw)

    # Assert
    assert result[0]["affected_image_digest"] is None


def test_vulnerability_without_image_or_package_has_null_fields():
    # Arrange
    raw = [{"id": "v1", "image": None, "package": None, "codeOwner": None}]

    # Act
    result = vulnerabilities.transform(raw)

    # Assert
    assert result[0]["image_name"] is None
    assert result[0]["affected_image_digest"] is None
    assert result[0]["package_name"] is None
    assert result[0]["code_owner_email"] is None


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


def test_vulnerability_status_is_normalized_from_sweet_title_case():
    # Arrange
    raw = [
        {"id": "1", "cve": "CVE-2026-0001", "status": "Open"},
        {"id": "2", "cve": "CVE-2026-0002", "status": "In Progress"},
        {"id": "3", "cve": "CVE-2026-0003", "status": "Ignored"},
        {"id": "4", "cve": "CVE-2026-0004", "status": None},
    ]

    # Act
    result = vulnerabilities.transform(raw)

    # Assert
    assert [v["status"] for v in result] == ["open", "in_progress", "ignored", None]


def test_vulnerability_status_filter_uses_sweet_title_case(mocker):
    # Arrange
    get_paginated = mocker.patch(
        "cartography.intel.sweet.api.get_paginated",
        return_value=[],
    )

    # Act
    vulnerabilities.get(mocker.MagicMock(), "https://eapi.sweet.security")

    # Assert
    assert get_paginated.call_args.args[3] == {"status": "Open,In Progress,Ignored"}
