from cartography.intel.tenable.was_findings import transform
from cartography.intel.tenable.was_findings import transform_plugins
from tests.data.tenable.assets import ASSET_ID_1
from tests.data.tenable.assets import ASSET_ID_2
from tests.data.tenable.was_findings import WAS_FINDING_ID_1
from tests.data.tenable.was_findings import WAS_FINDING_ID_2
from tests.data.tenable.was_findings import WAS_FINDINGS_DATA
from tests.data.tenable.was_findings import WAS_PLUGIN_ID_1
from tests.data.tenable.was_findings import WAS_PLUGIN_ID_2
from tests.data.tenable.was_findings import WAS_SCAN_UUID_1
from tests.data.tenable.was_findings import WAS_SCAN_UUID_2


# ---------------------------------------------------------------------------
# transform()
# ---------------------------------------------------------------------------


def test_transform_maps_all_fields():
    result = transform(WAS_FINDINGS_DATA)

    assert len(result) == 2

    f1 = next(r for r in result if r["id"] == WAS_FINDING_ID_1)
    assert f1["asset_uuid"] == ASSET_ID_1
    assert f1["plugin_id"] == WAS_PLUGIN_ID_1
    assert f1["scan_uuid"] == WAS_SCAN_UUID_1
    assert f1["url"] == "https://www.unixtimestamp.com/contact.php"
    assert "Current Version: 2.2.4" in f1["output"]
    assert f1["state"] == "OPEN"
    assert f1["severity"] == "MEDIUM"
    assert f1["severity_id"] == 2
    assert f1["severity_default_id"] == 2
    assert f1["severity_modification_type"] == "NONE"
    assert f1["first_found"] == "2024-02-01T16:08:41Z"
    assert f1["last_found"] == "2024-02-01T16:08:41Z"
    assert f1["indexed_at"] == "2024-02-01T16:08:41Z"
    assert f1["cve_id"] == "CVE-2015-9251"
    assert f1["cve_list"] == ["CVE-2015-9251"]
    assert f1["has_cve"] == "true"


def test_transform_cve_fields_no_cves():
    result = transform(WAS_FINDINGS_DATA)
    f2 = next(r for r in result if r["id"] == WAS_FINDING_ID_2)
    assert f2["asset_uuid"] == ASSET_ID_2
    assert f2["scan_uuid"] == WAS_SCAN_UUID_2
    assert f2["cve_id"] is None
    assert f2["cve_list"] == []
    assert f2["has_cve"] == "false"


def test_transform_skips_missing_finding_id():
    raw = [
        {"asset": {"uuid": "a-uuid"}, "plugin": {"id": 1}},
        {"finding_id": "f2", "asset": {"uuid": "a-uuid"}, "plugin": {"id": 2}},
    ]
    result = transform(raw)
    assert len(result) == 1
    assert result[0]["id"] == "f2"


def test_transform_skips_missing_asset_uuid():
    raw = [
        {"finding_id": "f1", "asset": {}, "plugin": {"id": 1}},
        {"finding_id": "f2", "asset": {"uuid": "a-uuid"}, "plugin": {"id": 2}},
    ]
    result = transform(raw)
    assert len(result) == 1
    assert result[0]["id"] == "f2"


def test_transform_skips_missing_plugin_id():
    raw = [
        {"finding_id": "f1", "asset": {"uuid": "a-uuid"}, "plugin": {}},
        {"finding_id": "f2", "asset": {"uuid": "a-uuid"}, "plugin": {"id": 99}},
    ]
    result = transform(raw)
    assert len(result) == 1
    assert result[0]["id"] == "f2"


def test_transform_null_scan_uuid_allowed():
    raw = [{"finding_id": "f1", "asset": {"uuid": "a-uuid"}, "plugin": {"id": 1}}]
    result = transform(raw)
    assert len(result) == 1
    assert result[0]["scan_uuid"] is None


def test_transform_empty_input():
    assert transform([]) == []


# ---------------------------------------------------------------------------
# transform_plugins()
# ---------------------------------------------------------------------------


def test_transform_plugins_basic():
    result = transform_plugins(WAS_FINDINGS_DATA)
    assert len(result) == 2

    p1 = next(r for r in result if r["id"] == WAS_PLUGIN_ID_1)
    assert p1["name"] == "jQuery 1.12.4 < 3.0.0 Cross-Site Scripting"
    assert p1["risk_factor"] == "MEDIUM"
    assert p1["type"] == "REMOTE"
    assert p1["cvss2_base_score"] == 4.3
    assert p1["cvss3_base_score"] == 6.1
    assert p1["cvss4_base_score"] == 6.9
    assert p1["vpr_score"] == 3
    assert p1["vpr_v2_score"] == 4.9
    assert p1["epss_score"] == 10.647
    assert p1["cve_ids"] == ["CVE-2015-9251"]
    assert p1["cwe_ids"] == ["79"]
    assert p1["in_the_news"] is False
    assert p1["exploited_by_malware"] is False


def test_transform_plugins_vpr_none_when_missing():
    result = transform_plugins(WAS_FINDINGS_DATA)
    p2 = next(r for r in result if r["id"] == WAS_PLUGIN_ID_2)
    assert p2["vpr_score"] is None
    assert p2["vpr_v2_score"] is None
    assert p2["cvss3_base_score"] is None
    assert p2["cve_ids"] == []
    assert p2["cwe_ids"] == []


def test_transform_plugins_deduplicates():
    raw = [
        {
            "finding_id": "f1",
            "asset": {"uuid": "a"},
            "plugin": {"id": 42, "name": "Plugin A", "cve": ["CVE-2021-1111"]},
        },
        {
            "finding_id": "f2",
            "asset": {"uuid": "b"},
            "plugin": {"id": 42, "name": "Plugin A", "cve": ["CVE-2021-1111"]},
        },
        {
            "finding_id": "f3",
            "asset": {"uuid": "c"},
            "plugin": {"id": 99, "name": "Plugin B"},
        },
    ]
    result = transform_plugins(raw)
    assert len(result) == 2
    assert {r["id"] for r in result} == {42, 99}


def test_transform_plugins_skips_missing_id():
    raw = [
        {"finding_id": "f1", "asset": {"uuid": "a"}, "plugin": {}},
        {"finding_id": "f2", "asset": {"uuid": "b"}, "plugin": {"id": 7}},
    ]
    result = transform_plugins(raw)
    assert len(result) == 1
    assert result[0]["id"] == 7


def test_transform_plugins_empty_input():
    assert transform_plugins([]) == []
