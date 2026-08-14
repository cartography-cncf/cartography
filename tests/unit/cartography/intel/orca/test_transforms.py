from datetime import datetime
from typing import Any

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
    result = assets.transform([ASSETS[0]], ORGANIZATION_ID)[0]

    assert result["id"] == ASSET_ID_1
    assert result["orca_id"] == INVENTORY_ID_1
    assert result["provider_id"] == "i-00000000000000001"
    assert result["cloud_account_id"] == "111122223333"
    assert result["zones"] == ["us-west-2a"]
    assert result["tags"] == ["environment=test", "owner=security"]
    assert result["first_seen"] == datetime.fromisoformat("2026-08-01T12:00:00+00:00")


def test_asset_transform_normalizes_stable_identifiers() -> None:
    raw = {
        **ASSETS[0],
        "id": f"  {INVENTORY_ID_1}  ",
        "asset_unique_id": "  asset-unique-1  ",
    }

    result = assets.transform([raw], ORGANIZATION_ID)[0]

    assert result["id"] == ASSET_ID_1
    assert result["orca_id"] == INVENTORY_ID_1
    assert result["asset_unique_id"] == "asset-unique-1"


@pytest.mark.parametrize("malformed_data", [None, [], "", 0, False])  # type: ignore[misc]
def test_asset_transform_rejects_falsey_non_object_data(
    malformed_data: Any,
) -> None:
    raw = {**ASSETS[0], "data": malformed_data}

    with pytest.raises(ValueError, match="Inventory.data must be an object"):
        assets.transform([raw], ORGANIZATION_ID)


def test_asset_transform_rejects_timestamp_without_utc_offset() -> None:
    raw = {
        **ASSETS[0],
        "data": {
            **ASSETS[0]["data"],
            "FirstSeen": {"value": "2026-08-01T12:00:00"},
        },
    }

    with pytest.raises(ValueError, match="must include a UTC offset"):
        assets.transform([raw], ORGANIZATION_ID)


def test_alert_query_requests_inventory_full_graph() -> None:
    query = alerts.build_query()

    assert query["query"]["models"] == ["Alert"]
    assert query["additional_models[]"] == ["Inventory"]
    assert query["full_graph_fetch"] == {"enabled": True}
    assert query["max_tier"] == 2


def test_alert_transform_uses_only_inventory_uuid_for_affects(caplog) -> None:
    result = alerts.transform(ALERTS, ORGANIZATION_ID)

    assert result[0]["asset_id"] == ASSET_ID_1
    assert result[0]["cve_ids"] == [CVE_ID_1]
    assert result[1]["asset_id"] is None
    assert "loaded without AFFECTS edges" in caplog.text


def test_alert_transform_unwraps_inventory_and_strips_cve_ids() -> None:
    raw = {
        **ALERTS[0],
        "Inventory": {"value": {"id": INVENTORY_ID_1}},
        "data": {
            **ALERTS[0]["data"],
            "CveIds": {"value": [f"  {CVE_ID_1.lower()}  "]},
        },
    }

    result = alerts.transform([raw], ORGANIZATION_ID)[0]

    assert result["asset_id"] == ASSET_ID_1
    assert result["cve_ids"] == [CVE_ID_1]


def test_alert_transform_normalizes_identifiers_and_timestamps() -> None:
    raw = {
        **ALERTS[0],
        "Inventory": {"id": f"  {INVENTORY_ID_1}  "},
        "data": {
            **ALERTS[0]["data"],
            "AlertId": {"value": "  orca-alert-1  "},
        },
    }

    result = alerts.transform([raw], ORGANIZATION_ID)[0]

    assert result["orca_id"] == "orca-alert-1"
    assert result["asset_id"] == ASSET_ID_1
    assert result["created_at"] == datetime.fromisoformat("2026-08-02T12:00:00+00:00")


@pytest.mark.parametrize("malformed_data", [None, [], "", 0, False])  # type: ignore[misc]
def test_alert_transform_rejects_falsey_non_object_data(
    malformed_data: Any,
) -> None:
    raw = {**ALERTS[0], "data": malformed_data}

    with pytest.raises(ValueError, match="Alert.data must be an object"):
        alerts.transform([raw], ORGANIZATION_ID)


def test_alert_transform_rejects_malformed_present_relationship_data() -> None:
    raw = {**ALERTS[0], "Inventory": "not-an-object"}

    with pytest.raises(ValueError, match="Alert.Inventory must be an object"):
        alerts.transform([raw], ORGANIZATION_ID)


def test_alert_transform_rejects_non_string_cve_values() -> None:
    raw = {
        **ALERTS[0],
        "data": {
            **ALERTS[0]["data"],
            "CveIds": {"value": [CVE_ID_1, {"id": "not-a-string"}]},
        },
    }

    with pytest.raises(ValueError, match="CVE fields must contain strings"):
        alerts.transform([raw], ORGANIZATION_ID)


def test_alert_transform_does_not_guess_between_multiple_inventory_records(
    caplog,
) -> None:
    raw = {
        **ALERTS[0],
        "Inventory": [{"id": INVENTORY_ID_1}, {"id": "another-inventory"}],
    }

    result = alerts.transform([raw], ORGANIZATION_ID)[0]

    assert result["asset_id"] is None
    assert "without AFFECTS edges" in caplog.text


def test_vulnerability_transform_is_stable_and_splits_explicit_cves() -> None:
    raw = {
        **VULNERABILITIES[0],
        "CveId": [CVE_ID_1.lower(), "CVE-2026-99999"],
    }

    first = vulnerabilities.transform([raw], ORGANIZATION_ID)
    second = vulnerabilities.transform([raw], ORGANIZATION_ID)

    assert [item["id"] for item in first] == [item["id"] for item in second]
    assert {item["cve_id"] for item in first} == {CVE_ID_1, "CVE-2026-99999"}
    assert {item["asset_unique_id"] for item in first} == {"asset-unique-1"}
    assert {item["inventory_id"] for item in first} == {
        "related-inventory-base-uuid-not-top-level-id",
    }
    assert all(item["patch_available"] is True for item in first)
    assert all(item["trending"] is False for item in first)
    assert all(
        item["first_seen"] == datetime.fromisoformat("2026-08-04T12:00:00+00:00")
        for item in first
    )


def test_vulnerability_identity_does_not_include_timestamps() -> None:
    changed = {**VULNERABILITIES[0], "FirstSeen": "2030-01-01T00:00:00Z"}

    original_id = vulnerabilities.transform(VULNERABILITIES, ORGANIZATION_ID)[0]["id"]
    changed_id = vulnerabilities.transform([changed], ORGANIZATION_ID)[0]["id"]

    assert changed_id == original_id


def test_vulnerability_identity_does_not_use_shared_package_base_uuid() -> None:
    # Orca's public flat response can reuse base_id_uuid across graph objects
    # even when the installed packages differ.
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

    results = vulnerabilities.transform([first, second], ORGANIZATION_ID)

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
    raw = {**VULNERABILITIES[0], **change}

    with pytest.raises((KeyError, ValueError)):
        vulnerabilities.transform([raw], ORGANIZATION_ID)


def test_asset_transform_rejects_duplicate_asset_unique_ids() -> None:
    duplicate = {**ASSETS[1], "asset_unique_id": ASSETS[0]["asset_unique_id"]}

    with pytest.raises(ValueError, match="duplicate asset_unique_id"):
        assets.transform([ASSETS[0], duplicate], ORGANIZATION_ID)


def test_vulnerability_transform_rejects_unknown_boolean_values() -> None:
    raw = {**VULNERABILITIES[0], "PatchAvailable": "perhaps"}

    with pytest.raises(ValueError, match="Unexpected Orca boolean"):
        vulnerabilities.transform([raw], ORGANIZATION_ID)


def test_vulnerability_transform_rejects_non_string_package_identity() -> None:
    raw = {
        **VULNERABILITIES[0],
        "InstalledPackage": {
            **VULNERABILITIES[0]["InstalledPackage"],
            "PURL": {"unexpected": "object"},
        },
    }

    with pytest.raises(ValueError, match="InstalledPackage.PURL"):
        vulnerabilities.transform([raw], ORGANIZATION_ID)


def test_vulnerability_query_matches_official_serving_layer_shape() -> None:
    query = vulnerabilities.build_query()

    assert query["query"]["models"] == ["VulnerabilityV2"]
    assert query["query"]["with"]["values"][0] == {
        "keys": ["Inventory"],
        "models": ["Inventory"],
        "type": "object",
        "operator": "has",
    }
    assert query["additional_models[]"] == ["InstalledPackage", "Inventory"]
    assert query["flat_json"] is True
