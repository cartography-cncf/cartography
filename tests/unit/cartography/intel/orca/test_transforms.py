import pytest

from cartography.intel.orca import alerts
from cartography.intel.orca import assets
from cartography.intel.orca import vulnerabilities
from tests.data.orca import ALERTS
from tests.data.orca import ASSET_ID_1
from tests.data.orca import ASSETS
from tests.data.orca import CVE_ID_1
from tests.data.orca import INVENTORY_ID_1
from tests.data.orca import ORGANIZATION_ID
from tests.data.orca import VULNERABILITIES


def test_asset_transform_namespaces_identity_and_flattens_wrapped_fields() -> None:
    # Act
    result = assets.transform([ASSETS[0]], ORGANIZATION_ID)[0]

    # Assert
    assert result["id"] == ASSET_ID_1
    assert result["orca_id"] == INVENTORY_ID_1
    assert result["provider_id"] == "i-00000000000000001"
    assert result["cloud_account_id"] == "111122223333"
    assert result["zones"] == ["us-west-2a"]
    assert result["tags"] == ["environment=test", "owner=security"]


def test_alert_query_requests_inventory_full_graph() -> None:
    # Act
    query = alerts.build_query()

    # Assert
    assert query["query"]["models"] == ["Alert"]
    assert query["additional_models[]"] == ["Inventory"]
    assert query["full_graph_fetch"] == {"enabled": True}
    assert query["max_tier"] == 2


def test_alert_transform_uses_only_inventory_uuid_for_affects(caplog) -> None:
    # Act
    result = alerts.transform(ALERTS, ORGANIZATION_ID)

    # Assert
    assert result[0]["asset_id"] == ASSET_ID_1
    assert result[0]["cve_ids"] == [CVE_ID_1]
    assert result[1]["asset_id"] is None
    assert "loaded without AFFECTS edges" in caplog.text


def test_alert_transform_unwraps_inventory_and_strips_cve_ids() -> None:
    # Arrange
    raw = {
        **ALERTS[0],
        "Inventory": {"value": {"id": INVENTORY_ID_1}},
        "data": {
            **ALERTS[0]["data"],
            "CveIds": {"value": [f"  {CVE_ID_1.lower()}  "]},
        },
    }

    # Act
    result = alerts.transform([raw], ORGANIZATION_ID)[0]

    # Assert
    assert result["asset_id"] == ASSET_ID_1
    assert result["cve_ids"] == [CVE_ID_1]


def test_alert_transform_does_not_guess_between_multiple_inventory_records(
    caplog,
) -> None:
    # Arrange
    raw = {
        **ALERTS[0],
        "Inventory": [{"id": INVENTORY_ID_1}, {"id": "another-inventory"}],
    }

    # Act
    result = alerts.transform([raw], ORGANIZATION_ID)[0]

    # Assert
    assert result["asset_id"] is None
    assert "without AFFECTS edges" in caplog.text


def test_vulnerability_transform_is_stable_and_splits_explicit_cves() -> None:
    # Arrange
    raw = {
        **VULNERABILITIES[0],
        "CveId": [CVE_ID_1.lower(), "CVE-2026-99999"],
    }

    # Act
    first = vulnerabilities.transform([raw], ORGANIZATION_ID)
    second = vulnerabilities.transform([raw], ORGANIZATION_ID)

    # Assert
    assert [item["id"] for item in first] == [item["id"] for item in second]
    assert {item["cve_id"] for item in first} == {CVE_ID_1, "CVE-2026-99999"}
    assert {item["asset_unique_id"] for item in first} == {"asset-unique-1"}
    assert {item["inventory_id"] for item in first} == {
        "related-inventory-base-uuid-not-top-level-id",
    }
    assert all(item["patch_available"] is True for item in first)
    assert all(item["trending"] is False for item in first)


def test_vulnerability_identity_does_not_include_timestamps() -> None:
    # Arrange
    changed = {**VULNERABILITIES[0], "FirstSeen": "2030-01-01T00:00:00Z"}

    # Act
    original_id = vulnerabilities.transform(VULNERABILITIES, ORGANIZATION_ID)[0]["id"]
    changed_id = vulnerabilities.transform([changed], ORGANIZATION_ID)[0]["id"]

    # Assert
    assert changed_id == original_id


def test_vulnerability_identity_does_not_use_shared_package_base_uuid() -> None:
    # Arrange: mirror Orca's public flat response, where base_id_uuid can be
    # shared by graph objects even though the installed packages differ.
    first = {
        **VULNERABILITIES[0],
        "InstalledPackage": {
            **VULNERABILITIES[0]["InstalledPackage"],
            "PURL": "pkg:deb/example/first@1.0.0",
        },
    }
    second = {
        **VULNERABILITIES[0],
        "InstalledPackage": {
            **VULNERABILITIES[0]["InstalledPackage"],
            "PURL": "pkg:deb/example/second@2.0.0",
        },
    }

    # Act
    results = vulnerabilities.transform([first, second], ORGANIZATION_ID)

    # Assert
    assert len({result["id"] for result in results}) == 2
    assert {result["package_base_id_uuid"] for result in results} == {
        "vulnerability-base-1",
    }
    assert {result["package_id"] for result in results} == {None}


@pytest.mark.parametrize(
    "change",
    [
        {"CveId": "GHSA-not-a-cve"},
        {"Inventory": {}},
    ],
)  # type: ignore[misc]
def test_vulnerability_transform_rejects_missing_canonical_identity(change) -> None:
    # Arrange
    raw = {**VULNERABILITIES[0], **change}

    # Act and assert
    with pytest.raises((KeyError, ValueError)):
        vulnerabilities.transform([raw], ORGANIZATION_ID)


def test_asset_transform_rejects_duplicate_asset_unique_ids() -> None:
    # Arrange
    duplicate = {**ASSETS[1], "asset_unique_id": ASSETS[0]["asset_unique_id"]}

    # Act and assert
    with pytest.raises(ValueError, match="duplicate asset_unique_id"):
        assets.transform([ASSETS[0], duplicate], ORGANIZATION_ID)


def test_vulnerability_transform_rejects_unknown_boolean_values() -> None:
    # Arrange
    raw = {**VULNERABILITIES[0], "PatchAvailable": "perhaps"}

    # Act and assert
    with pytest.raises(ValueError, match="Unexpected Orca boolean"):
        vulnerabilities.transform([raw], ORGANIZATION_ID)


def test_vulnerability_query_matches_official_serving_layer_shape() -> None:
    # Act
    query = vulnerabilities.build_query()

    # Assert
    assert query["query"]["models"] == ["VulnerabilityV2"]
    assert query["query"]["with"]["values"][0] == {
        "keys": ["Inventory"],
        "models": ["Inventory"],
        "type": "object",
        "operator": "has",
    }
    assert query["additional_models[]"] == ["InstalledPackage", "Inventory"]
    assert query["flat_json"] is True
