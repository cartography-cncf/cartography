from copy import deepcopy
from datetime import datetime
from typing import Any

import pytest

from cartography.intel.orca import alerts
from cartography.intel.orca import vulnerabilities
from tests.data.orca import ALERTS
from tests.data.orca import ASSET_UNIQUE_ID_1
from tests.data.orca import ASSET_UNIQUE_ID_2
from tests.data.orca import CVE_ID_1
from tests.data.orca import INVENTORY_ID_1
from tests.data.orca import ORGANIZATION_ID
from tests.data.orca import PROVIDER_ID_1
from tests.data.orca import PROVIDER_ID_2
from tests.data.orca import TARGET_ARN_1
from tests.data.orca import VULNERABILITIES

TARGET_FIELDS = {
    "target_orca_inventory_id",
    "target_orca_asset_unique_id",
    "target_provider_id",
    "target_arn",
    "target_cloud_provider",
    "target_cloud_account_id",
    "target_region",
    "target_name",
    "target_type",
}


def test_finding_queries_do_not_request_a_standalone_inventory_feed() -> None:
    # Act
    queries = [alerts.build_query(), vulnerabilities.build_query()]

    # Assert
    assert [query["query"]["models"] for query in queries] == [
        ["Alert"],
        ["VulnerabilityV2"],
    ]
    assert all(query["query"]["models"] != ["Inventory"] for query in queries)


def test_alert_query_requests_related_inventory_context() -> None:
    # Act
    query = alerts.build_query()

    # Assert
    assert query["additional_models[]"] == ["Inventory"]
    assert query["full_graph_fetch"] == {"enabled": True}
    assert query["max_tier"] == 2


def test_alert_transform_retains_exact_target_context_and_missing_target(
    caplog,
) -> None:
    # Act
    result = alerts.transform(ALERTS, ORGANIZATION_ID)

    # Assert
    assert TARGET_FIELDS <= result[0].keys()
    assert result[0]["target_orca_inventory_id"] == INVENTORY_ID_1
    assert result[0]["target_orca_asset_unique_id"] == ASSET_UNIQUE_ID_1
    assert result[0]["target_provider_id"] == PROVIDER_ID_1
    assert result[0]["target_arn"] == TARGET_ARN_1
    assert result[0]["target_cloud_provider"] == "aws"
    assert result[0]["target_cloud_account_id"] == "111122223333"
    assert result[0]["target_region"] == "us-west-2"
    assert result[0]["target_name"] == "synthetic-app-server"
    assert result[0]["target_type"] == "AwsEc2Instance"
    assert result[0]["cve_ids"] == [CVE_ID_1]

    assert TARGET_FIELDS <= result[1].keys()
    assert result[1]["target_orca_inventory_id"] is None
    assert result[1]["target_orca_asset_unique_id"] is None
    assert result[1]["target_provider_id"] is None
    assert result[1]["target_arn"] is None
    assert result[1]["target_name"] == "removed-asset"
    assert result[1]["target_type"] == "Unknown"
    assert "without exact target identifiers" in caplog.text


def test_alert_transform_unwraps_inventory_and_strips_cve_ids() -> None:
    # Arrange
    raw = deepcopy(ALERTS[0])
    raw["Inventory"] = {"value": raw["Inventory"]}
    raw["data"]["CveIds"] = {"value": [f"  {CVE_ID_1.lower()}  "]}

    # Act
    result = alerts.transform([raw], ORGANIZATION_ID)[0]

    # Assert
    assert result["target_orca_inventory_id"] == INVENTORY_ID_1
    assert result["cve_ids"] == [CVE_ID_1]


def test_alert_transform_reads_wrapper_fields_before_nested_data() -> None:
    # Arrange
    raw = deepcopy(ALERTS[0])
    raw["Inventory"].pop("id")
    raw["Inventory"]["base_id_uuid"] = "wrapper-inventory-id"
    raw["Inventory"]["UiUniqueField"] = "wrapper-provider-id"

    # Act
    result = alerts.transform([raw], ORGANIZATION_ID)[0]

    # Assert
    assert result["target_orca_inventory_id"] == "wrapper-inventory-id"
    assert result["target_provider_id"] == "wrapper-provider-id"


def test_alert_transform_normalizes_identifiers_and_timestamps() -> None:
    # Arrange
    raw = deepcopy(ALERTS[0])
    raw["Inventory"]["id"] = f"  {INVENTORY_ID_1}  "
    raw["Inventory"]["asset_unique_id"] = f"  {ASSET_UNIQUE_ID_1}  "
    raw["data"]["AlertId"] = {"value": "  orca-alert-1  "}

    # Act
    result = alerts.transform([raw], ORGANIZATION_ID)[0]

    # Assert
    assert result["orca_id"] == "orca-alert-1"
    assert result["target_orca_inventory_id"] == INVENTORY_ID_1
    assert result["target_orca_asset_unique_id"] == ASSET_UNIQUE_ID_1
    assert result["created_at"] == datetime.fromisoformat("2026-08-02T12:00:00+00:00")


@pytest.mark.parametrize("malformed_data", [None, [], "", 0, False])  # type: ignore[misc]
def test_alert_transform_rejects_falsey_non_object_data(
    malformed_data: Any,
) -> None:
    # Arrange
    raw = {**ALERTS[0], "data": malformed_data}

    # Act and assert
    with pytest.raises(ValueError, match="Alert.data must be an object"):
        alerts.transform([raw], ORGANIZATION_ID)


def test_alert_transform_rejects_malformed_present_relationship_data() -> None:
    # Arrange
    raw = {**ALERTS[0], "Inventory": "not-an-object"}

    # Act and assert
    with pytest.raises(ValueError, match="Alert.Inventory must be an object"):
        alerts.transform([raw], ORGANIZATION_ID)


def test_alert_transform_rejects_non_string_cve_values() -> None:
    # Arrange
    raw = deepcopy(ALERTS[0])
    raw["data"]["CveIds"] = {"value": [CVE_ID_1, {"id": "not-a-string"}]}

    # Act and assert
    with pytest.raises(ValueError, match="CVE fields must contain strings"):
        alerts.transform([raw], ORGANIZATION_ID)


def test_alert_transform_does_not_choose_an_ambiguous_inventory(caplog) -> None:
    # Arrange
    raw = deepcopy(ALERTS[0])
    raw["Inventory"] = [
        raw["Inventory"],
        {"id": "another-inventory", "asset_unique_id": ASSET_UNIQUE_ID_2},
    ]

    # Act
    result = alerts.transform([raw], ORGANIZATION_ID)[0]

    # Assert
    assert result["target_orca_inventory_id"] is None
    assert result["target_orca_asset_unique_id"] is None
    assert result["target_provider_id"] is None
    assert result["target_name"] == "synthetic-app-server"
    assert "without exact target identifiers" in caplog.text


def test_vulnerability_transform_is_stable_and_splits_explicit_cves() -> None:
    # Arrange
    raw = {**VULNERABILITIES[0], "CveId": [CVE_ID_1.lower(), "CVE-2026-99999"]}

    # Act
    first = vulnerabilities.transform([raw], ORGANIZATION_ID)
    second = vulnerabilities.transform([raw], ORGANIZATION_ID)

    # Assert
    assert [item["id"] for item in first] == [item["id"] for item in second]
    assert {item["cve_id"] for item in first} == {CVE_ID_1, "CVE-2026-99999"}
    assert {item["target_orca_asset_unique_id"] for item in first} == {
        ASSET_UNIQUE_ID_1
    }
    assert {item["target_orca_inventory_id"] for item in first} == {
        "related-inventory-base-uuid-not-top-level-id",
    }
    assert {item["target_provider_id"] for item in first} == {PROVIDER_ID_1}
    assert {item["target_arn"] for item in first} == {TARGET_ARN_1}
    assert {item["target_name"] for item in first} == {"synthetic-app-server"}
    assert all(item["patch_available"] is True for item in first)
    assert all(item["trending"] is False for item in first)
    assert all(
        item["first_seen"] == datetime.fromisoformat("2026-08-04T12:00:00+00:00")
        for item in first
    )


def test_vulnerability_identity_ignores_nonidentity_target_context() -> None:
    # Arrange
    changed = deepcopy(VULNERABILITIES[0])
    changed["FirstSeen"] = "2030-01-01T00:00:00Z"
    changed["Inventory"]["Name"] = "renamed-asset"
    changed["Inventory"]["UiUniqueField"] = PROVIDER_ID_2

    # Act
    original_id = vulnerabilities.transform(VULNERABILITIES, ORGANIZATION_ID)[0]["id"]
    changed_id = vulnerabilities.transform([changed], ORGANIZATION_ID)[0]["id"]

    # Assert
    assert changed_id == original_id


def test_vulnerability_identity_changes_with_target_asset_unique_id() -> None:
    # Arrange
    changed = deepcopy(VULNERABILITIES[0])
    changed["Inventory"]["AssetUniqueId"] = ASSET_UNIQUE_ID_2

    # Act
    original_id = vulnerabilities.transform(VULNERABILITIES, ORGANIZATION_ID)[0]["id"]
    changed_id = vulnerabilities.transform([changed], ORGANIZATION_ID)[0]["id"]

    # Assert
    assert changed_id != original_id


def test_vulnerability_identity_does_not_use_shared_package_base_uuid() -> None:
    # Arrange
    # Orca's public flat response can reuse base_id_uuid across graph objects
    # even when the installed packages differ.
    first = deepcopy(VULNERABILITIES[0])
    first["InstalledPackage"]["PURL"] = "pkg:deb/example/first@1.0.0"
    second = deepcopy(VULNERABILITIES[0])
    second["InstalledPackage"]["PURL"] = "pkg:deb/example/second@2.0.0"

    # Act
    results = vulnerabilities.transform([first, second], ORGANIZATION_ID)

    # Assert
    assert len({result["id"] for result in results}) == 2
    assert {result["package_base_id_uuid"] for result in results} == {
        "vulnerability-base-1",
    }
    assert {result["package_id"] for result in results} == {None}


def test_vulnerability_identity_separates_package_identifier_namespaces() -> None:
    # Arrange
    package_id = deepcopy(VULNERABILITIES[0])
    package_id["InstalledPackage"] = {"id": "same-value"}
    package_purl = deepcopy(VULNERABILITIES[0])
    package_purl["InstalledPackage"] = {"PURL": "same-value"}

    # Act
    results = vulnerabilities.transform([package_id, package_purl], ORGANIZATION_ID)

    # Assert
    assert len({result["id"] for result in results}) == 2


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


def test_vulnerability_transform_rejects_unknown_boolean_values() -> None:
    # Arrange
    raw = {**VULNERABILITIES[0], "PatchAvailable": "perhaps"}

    # Act and assert
    with pytest.raises(ValueError, match="Unexpected Orca boolean"):
        vulnerabilities.transform([raw], ORGANIZATION_ID)


def test_vulnerability_transform_rejects_non_string_package_identity() -> None:
    # Arrange
    raw = deepcopy(VULNERABILITIES[0])
    raw["InstalledPackage"]["PURL"] = {"unexpected": "object"}

    # Act and assert
    with pytest.raises(ValueError, match="InstalledPackage.PURL"):
        vulnerabilities.transform([raw], ORGANIZATION_ID)


def test_vulnerability_query_matches_official_serving_layer_shape() -> None:
    # Act
    query = vulnerabilities.build_query()

    # Assert
    assert query["query"]["with"]["values"][0] == {
        "keys": ["Inventory"],
        "models": ["Inventory"],
        "type": "object",
        "operator": "has",
    }
    assert query["additional_models[]"] == ["InstalledPackage", "Inventory"]
    assert query["flat_json"] is True
