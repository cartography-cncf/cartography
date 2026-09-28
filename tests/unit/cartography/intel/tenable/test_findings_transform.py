import pytest

from cartography.intel.tenable.findings import get
from cartography.intel.tenable.findings import transform
from cartography.intel.tenable.findings import transform_plugins
from cartography.intel.tenable.findings import transform_scans
from tests.data.tenable.assets import ASSET_ID_1
from tests.data.tenable.findings import FINDING_ID_1
from tests.data.tenable.findings import FINDING_ID_2
from tests.data.tenable.findings import FINDING_ID_3
from tests.data.tenable.findings import FINDINGS_DATA
from tests.data.tenable.findings import PLUGIN_ID_1
from tests.data.tenable.findings import PLUGIN_ID_2
from tests.data.tenable.findings import PLUGIN_ID_3
from tests.data.tenable.findings import SCAN_UUID_1
from tests.data.tenable.findings import SCAN_UUID_2


def test_get_builds_findings_export_filter(mocker):
    # Arrange
    mock_export = mocker.patch(
        "cartography.intel.tenable.findings.export_and_download",
        return_value=FINDINGS_DATA,
    )

    # Act
    result = get(mocker.MagicMock(), "https://cloud.tenable.com", 123456789)

    # Assert
    assert result == FINDINGS_DATA
    assert mock_export.call_args.args[4] == {
        "num_assets": 500,
        "filters": {
            "last_found": 123456789,
            "state": ["OPEN", "REOPENED", "FIXED"],
        },
    }


# ---------------------------------------------------------------------------
# transform()
# ---------------------------------------------------------------------------


def test_transform_maps_all_fields():
    # Act
    result = transform(FINDINGS_DATA)

    # Assert
    assert len(result) == 3

    f1 = next(r for r in result if r["id"] == FINDING_ID_1)
    assert f1["asset_uuid"] == ASSET_ID_1
    assert f1["plugin_id"] == PLUGIN_ID_1
    assert f1["scan_uuid"] == SCAN_UUID_1
    assert f1["severity"] == "high"
    assert f1["severity_id"] == 3
    assert f1["severity_default_id"] == 3
    assert f1["severity_modification_type"] == "NONE"
    assert f1["state"] == "OPEN"
    assert f1["first_found"] == "2022-11-08T19:18:10.472Z"
    assert f1["last_found"] == "2023-05-04T05:03:13.737Z"
    assert f1["indexed"] == "2023-05-04T05:13:40.809406Z"
    assert f1["source"] == "NESSUS"
    assert (
        f1["output"]
        == "Microsoft SharePoint Enterprise Server 2016 - KB5002113 missing."
    )
    assert f1["resurfaced_date"] == "2024-11-27T11:56:24.384Z"
    assert f1["time_taken_to_fix"] == "3045760"
    # Port flattened
    assert f1["port"] == 445
    assert f1["protocol"] == "TCP"
    assert f1["service"] == "cifs"
    # CVE fields: finding has CVEs
    assert f1["cve_id"] == "CVE-2022-21837"
    assert set(f1["cve_list"]) == {
        "CVE-2022-21837",
        "CVE-2022-21840",
        "CVE-2022-21842",
    }
    assert f1["has_cve"] == "true"


def test_transform_cve_fields_no_cves():
    # Act
    result = transform(FINDINGS_DATA)

    # Assert
    f2 = next(r for r in result if r["id"] == FINDING_ID_2)
    assert f2["cve_id"] is None
    assert f2["cve_list"] == []
    assert f2["has_cve"] == "false"


def test_transform_port_zero_and_null_service():
    # Act
    result = transform(FINDINGS_DATA)

    # Assert
    f3 = next(r for r in result if r["id"] == FINDING_ID_3)
    assert f3["port"] == 0
    assert f3["protocol"] == "TCP"
    assert f3["service"] is None


@pytest.mark.parametrize(
    "raw_finding",
    [
        {"finding_id": "f1", "asset": {}, "plugin": {"id": 1}},
        {"asset": {"uuid": "a-uuid"}, "plugin": {"id": 1}},
        {"finding_id": "f1", "asset": {"uuid": "a-uuid"}, "plugin": {}},
    ],
)
def test_transform_rejects_missing_required_identifiers(raw_finding):
    # Act and assert
    with pytest.raises(KeyError):
        transform([raw_finding])


@pytest.mark.parametrize(
    "raw_finding",
    [
        {"finding_id": "f1", "asset": {"uuid": None}, "plugin": {"id": 1}},
        {"finding_id": "", "asset": {"uuid": "a-uuid"}, "plugin": {"id": 1}},
        {"finding_id": "f1", "asset": {"uuid": "a-uuid"}, "plugin": {"id": None}},
    ],
)
def test_transform_rejects_null_or_empty_required_identifiers(raw_finding):
    # Act and assert
    with pytest.raises(ValueError, match="Tenable finding requires"):
        transform([raw_finding])


def test_transform_null_scan_uuid_allowed():
    """A finding with no scan block should still be included; scan_uuid will be None."""
    # Arrange
    raw = [{"finding_id": "f1", "asset": {"uuid": "a-uuid"}, "plugin": {"id": 1}}]

    # Act
    result = transform(raw)

    # Assert
    assert len(result) == 1
    assert result[0]["scan_uuid"] is None


def test_transform_empty_input():
    # Act and assert
    assert transform([]) == []


# ---------------------------------------------------------------------------
# transform_plugins()
# ---------------------------------------------------------------------------


def test_transform_plugins_basic():
    # Act
    result = transform_plugins(FINDINGS_DATA)

    # Assert
    assert len(result) == 3

    p1 = next(r for r in result if r["id"] == PLUGIN_ID_1)
    assert (
        p1["name"]
        == "Security Updates for Microsoft SharePoint Server 2016 (January 2022)"
    )
    assert p1["family"] == "Windows : Microsoft Bulletins"
    assert p1["risk_factor"] == "high"
    assert p1["cvss3_base_score"] == 8.8
    assert p1["vpr_score"] == 6.7
    assert p1["epss_score"] == 10.647
    assert set(p1["cve_list"]) == {"CVE-2022-21837", "CVE-2022-21840", "CVE-2022-21842"}


def test_transform_plugins_vpr_none_when_missing():
    # Act
    result = transform_plugins(FINDINGS_DATA)

    # Assert
    p2 = next(r for r in result if r["id"] == PLUGIN_ID_2)
    assert p2["vpr_score"] is None


def test_transform_plugins_empty_cve_list():
    # Act
    result = transform_plugins(FINDINGS_DATA)

    # Assert
    p3 = next(r for r in result if r["id"] == PLUGIN_ID_3)
    assert p3["cve_list"] == []


def test_transform_plugins_deduplicates():
    # Arrange
    raw = [
        {
            "finding_id": "f1",
            "asset": {"uuid": "a"},
            "plugin": {"id": 42, "name": "Plugin A"},
        },
        {
            "finding_id": "f2",
            "asset": {"uuid": "b"},
            "plugin": {"id": 42, "name": "Plugin A"},
        },
        {
            "finding_id": "f3",
            "asset": {"uuid": "c"},
            "plugin": {"id": 99, "name": "Plugin B"},
        },
    ]

    # Act
    result = transform_plugins(raw)

    # Assert
    assert len(result) == 2
    assert {r["id"] for r in result} == {42, 99}


def test_transform_plugins_skips_missing_id():
    # Arrange
    raw = [
        {"finding_id": "f1", "asset": {"uuid": "a"}, "plugin": {}},
        {"finding_id": "f2", "asset": {"uuid": "b"}, "plugin": {"id": 7}},
    ]

    # Act
    result = transform_plugins(raw)

    # Assert
    assert len(result) == 1
    assert result[0]["id"] == 7


def test_transform_plugins_empty_input():
    # Act and assert
    assert transform_plugins([]) == []


# ---------------------------------------------------------------------------
# transform_scans()
# ---------------------------------------------------------------------------


def test_transform_scans_basic():
    # Act
    result = transform_scans(FINDINGS_DATA)

    # Assert
    # FINDING_ID_1 and FINDING_ID_3 share SCAN_UUID_1, so only two scan nodes exist
    assert len(result) == 2

    s1 = next(r for r in result if r["id"] == SCAN_UUID_1)
    assert s1["schedule_uuid"] == "461e4ebc-b309-face-6fa1-afa4ba163cb6d84b9dc0a0dc5020"
    assert s1["started_at"] == "2023-05-03T14:14:02.387Z"
    assert s1["last_scan_target"] == "192.0.2.58"

    s2 = next(r for r in result if r["id"] == SCAN_UUID_2)
    assert s2["last_scan_target"] == "192.0.2.58"


def test_transform_scans_deduplicates():
    # Arrange
    raw = [
        {
            "finding_id": "f1",
            "scan": {"uuid": "scan-aaa", "last_scan_target": "10.0.0.1"},
        },
        {
            "finding_id": "f2",
            "scan": {"uuid": "scan-aaa", "last_scan_target": "10.0.0.1"},
        },
        {
            "finding_id": "f3",
            "scan": {"uuid": "scan-bbb", "last_scan_target": "10.0.0.2"},
        },
    ]

    # Act
    result = transform_scans(raw)

    # Assert
    assert len(result) == 2
    assert {r["id"] for r in result} == {"scan-aaa", "scan-bbb"}


def test_transform_scans_skips_missing_uuid():
    # Arrange
    raw = [
        {"finding_id": "f1", "scan": {}},
        {"finding_id": "f2"},
        {"finding_id": "f3", "scan": {"uuid": "scan-xyz"}},
    ]

    # Act
    result = transform_scans(raw)

    # Assert
    assert len(result) == 1
    assert result[0]["id"] == "scan-xyz"


def test_transform_scans_empty_input():
    # Act and assert
    assert transform_scans([]) == []
