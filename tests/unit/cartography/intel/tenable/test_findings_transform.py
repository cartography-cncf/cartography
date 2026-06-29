from cartography.intel.tenable.findings import transform
from cartography.intel.tenable.findings import transform_cves
from cartography.intel.tenable.findings import transform_plugins
from cartography.intel.tenable.findings import transform_scans
from tests.data.tenable.assets import ASSET_ID_1
from tests.data.tenable.assets import SCOPED_ASSET_ID_1
from tests.data.tenable.assets import tenable_id
from tests.data.tenable.assets import TENABLE_TENANT_ID
from tests.data.tenable.findings import CVE_ID_1
from tests.data.tenable.findings import CVE_ID_2
from tests.data.tenable.findings import CVE_ID_3
from tests.data.tenable.findings import FINDING_ID_1
from tests.data.tenable.findings import FINDING_ID_2
from tests.data.tenable.findings import FINDING_ID_3
from tests.data.tenable.findings import FINDINGS_DATA
from tests.data.tenable.findings import PLUGIN_ID_1
from tests.data.tenable.findings import PLUGIN_ID_2
from tests.data.tenable.findings import PLUGIN_ID_3
from tests.data.tenable.findings import SCAN_UUID_1
from tests.data.tenable.findings import SCAN_UUID_2
from tests.data.tenable.findings import SCOPED_CVE_ID_1
from tests.data.tenable.findings import SCOPED_CVE_ID_2
from tests.data.tenable.findings import SCOPED_CVE_ID_3
from tests.data.tenable.findings import SCOPED_FINDING_ID_1
from tests.data.tenable.findings import SCOPED_PLUGIN_ID_1
from tests.data.tenable.findings import SCOPED_SCAN_UUID_1

# ---------------------------------------------------------------------------
# transform()
# ---------------------------------------------------------------------------


def test_transform_maps_all_fields():
    result = transform(FINDINGS_DATA, TENABLE_TENANT_ID)

    assert len(result) == 3

    f1 = next(r for r in result if r["id"] == SCOPED_FINDING_ID_1)
    assert f1["finding_id"] == FINDING_ID_1
    assert f1["asset_uuid"] == ASSET_ID_1
    assert f1["asset_id"] == SCOPED_ASSET_ID_1
    assert f1["plugin_id"] == PLUGIN_ID_1
    assert f1["plugin_node_id"] == SCOPED_PLUGIN_ID_1
    assert f1["scan_uuid"] == SCAN_UUID_1
    assert f1["scan_node_id"] == SCOPED_SCAN_UUID_1
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
    assert f1["cve_node_ids"] == [SCOPED_CVE_ID_1, SCOPED_CVE_ID_2, SCOPED_CVE_ID_3]


def test_transform_cve_fields_no_cves():
    result = transform(FINDINGS_DATA, TENABLE_TENANT_ID)
    f2 = next(r for r in result if r["finding_id"] == FINDING_ID_2)
    assert f2["cve_node_ids"] == []


def test_transform_port_zero_and_null_service():
    result = transform(FINDINGS_DATA, TENABLE_TENANT_ID)
    f3 = next(r for r in result if r["finding_id"] == FINDING_ID_3)
    assert f3["port"] == 0
    assert f3["protocol"] == "TCP"
    assert f3["service"] is None


def test_transform_skips_missing_asset_uuid():
    raw = [
        {"finding_id": "f1", "asset": {}, "plugin": {"id": 1}},
        {"finding_id": "f2", "asset": {"uuid": "a-uuid"}, "plugin": {"id": 2}},
    ]
    result = transform(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    assert result[0]["id"] == tenable_id("f2")
    assert result[0]["finding_id"] == "f2"


def test_transform_skips_missing_finding_id():
    raw = [
        {"asset": {"uuid": "a-uuid"}, "plugin": {"id": 1}},
        {"finding_id": "f2", "asset": {"uuid": "a-uuid"}, "plugin": {"id": 2}},
    ]
    result = transform(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    assert result[0]["id"] == tenable_id("f2")
    assert result[0]["finding_id"] == "f2"


def test_transform_skips_missing_plugin_id():
    raw = [
        {"finding_id": "f1", "asset": {"uuid": "a-uuid"}, "plugin": {}},
        {"finding_id": "f2", "asset": {"uuid": "a-uuid"}, "plugin": {"id": 99}},
    ]
    result = transform(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    assert result[0]["id"] == tenable_id("f2")
    assert result[0]["finding_id"] == "f2"


def test_transform_null_scan_uuid_allowed():
    """A finding with no scan block should still be included; scan_uuid will be None."""
    raw = [{"finding_id": "f1", "asset": {"uuid": "a-uuid"}, "plugin": {"id": 1}}]
    result = transform(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    assert result[0]["scan_uuid"] is None
    assert result[0]["scan_node_id"] is None


def test_transform_empty_input():
    assert transform([], TENABLE_TENANT_ID) == []


# ---------------------------------------------------------------------------
# transform_plugins()
# ---------------------------------------------------------------------------


def test_transform_plugins_basic():
    result = transform_plugins(FINDINGS_DATA, TENABLE_TENANT_ID)
    assert len(result) == 3

    p1 = next(r for r in result if r["id"] == SCOPED_PLUGIN_ID_1)
    assert p1["plugin_id"] == PLUGIN_ID_1
    assert (
        p1["name"]
        == "Security Updates for Microsoft SharePoint Server 2016 (January 2022)"
    )
    assert p1["family"] == "Windows : Microsoft Bulletins"
    assert p1["risk_factor"] == "high"
    assert p1["cvss3_base_score"] == 8.8
    assert p1["vpr_score"] == 6.7
    assert p1["epss_score"] == 10.647
    assert p1["cve_list"] == [CVE_ID_1, CVE_ID_2, CVE_ID_3]
    assert p1["cve_node_ids"] == [SCOPED_CVE_ID_1, SCOPED_CVE_ID_2, SCOPED_CVE_ID_3]


def test_transform_plugins_vpr_none_when_missing():
    result = transform_plugins(FINDINGS_DATA, TENABLE_TENANT_ID)
    p2 = next(r for r in result if r["plugin_id"] == PLUGIN_ID_2)
    assert p2["vpr_score"] is None


def test_transform_plugins_empty_cve_list():
    result = transform_plugins(FINDINGS_DATA, TENABLE_TENANT_ID)
    p3 = next(r for r in result if r["plugin_id"] == PLUGIN_ID_3)
    assert p3["cve_list"] == []
    assert p3["cve_node_ids"] == []


def test_transform_plugins_deduplicates():
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
    result = transform_plugins(raw, TENABLE_TENANT_ID)
    assert len(result) == 2
    assert {r["id"] for r in result} == {tenable_id(42), tenable_id(99)}
    assert {r["plugin_id"] for r in result} == {42, 99}


def test_transform_plugins_skips_missing_id():
    raw = [
        {"finding_id": "f1", "asset": {"uuid": "a"}, "plugin": {}},
        {"finding_id": "f2", "asset": {"uuid": "b"}, "plugin": {"id": 7}},
    ]
    result = transform_plugins(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    assert result[0]["id"] == tenable_id(7)
    assert result[0]["plugin_id"] == 7


def test_transform_plugins_empty_input():
    assert transform_plugins([], TENABLE_TENANT_ID) == []


# ---------------------------------------------------------------------------
# transform_cves()
# ---------------------------------------------------------------------------


def test_transform_cves_deduplicates_plugin_cves():
    result = transform_cves(FINDINGS_DATA, TENABLE_TENANT_ID)

    assert result == [
        {"id": SCOPED_CVE_ID_1, "cve_id": CVE_ID_1},
        {"id": SCOPED_CVE_ID_2, "cve_id": CVE_ID_2},
        {"id": SCOPED_CVE_ID_3, "cve_id": CVE_ID_3},
    ]


def test_transform_cves_filters_non_cve_values():
    raw = [
        {
            "finding_id": "f1",
            "asset": {"uuid": "a"},
            "plugin": {
                "id": 42,
                "cve": [CVE_ID_1, "GHSA-1234", None, CVE_ID_1],
            },
        },
    ]

    result = transform_cves(raw, TENABLE_TENANT_ID)

    assert result == [{"id": SCOPED_CVE_ID_1, "cve_id": CVE_ID_1}]


def test_transform_cves_empty_input():
    assert transform_cves([], TENABLE_TENANT_ID) == []


# ---------------------------------------------------------------------------
# transform_scans()
# ---------------------------------------------------------------------------


def test_transform_scans_basic():
    result = transform_scans(FINDINGS_DATA, TENABLE_TENANT_ID)
    # FINDING_ID_1 and FINDING_ID_3 share SCAN_UUID_1 — only two scan nodes
    assert len(result) == 2

    s1 = next(r for r in result if r["id"] == SCOPED_SCAN_UUID_1)
    assert s1["scan_uuid"] == SCAN_UUID_1
    assert s1["schedule_uuid"] == "461e4ebc-b309-face-6fa1-afa4ba163cb6d84b9dc0a0dc5020"
    assert s1["started_at"] == "2023-05-03T14:14:02.387Z"
    assert s1["last_scan_target"] == "192.0.2.58"

    s2 = next(r for r in result if r["scan_uuid"] == SCAN_UUID_2)
    assert s2["last_scan_target"] == "192.0.2.58"


def test_transform_scans_deduplicates():
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
    result = transform_scans(raw, TENABLE_TENANT_ID)
    assert len(result) == 2
    assert {r["id"] for r in result} == {
        tenable_id("scan-aaa"),
        tenable_id("scan-bbb"),
    }


def test_transform_scans_skips_missing_uuid():
    raw = [
        {"finding_id": "f1", "scan": {}},
        {"finding_id": "f2"},
        {"finding_id": "f3", "scan": {"uuid": "scan-xyz"}},
    ]
    result = transform_scans(raw, TENABLE_TENANT_ID)
    assert len(result) == 1
    assert result[0]["id"] == tenable_id("scan-xyz")
    assert result[0]["scan_uuid"] == "scan-xyz"


def test_transform_scans_empty_input():
    assert transform_scans([], TENABLE_TENANT_ID) == []
