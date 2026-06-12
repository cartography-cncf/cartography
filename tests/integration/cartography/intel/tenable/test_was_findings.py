import cartography.intel.tenable.assets
import cartography.intel.tenable.was_findings
from tests.data.tenable.assets import ASSET_ID_1
from tests.data.tenable.assets import ASSET_ID_2
from tests.data.tenable.assets import ASSETS_DATA
from tests.data.tenable.assets import TENABLE_TENANT_ID
from tests.data.tenable.was_findings import WAS_FINDING_ID_1
from tests.data.tenable.was_findings import WAS_FINDING_ID_2
from tests.data.tenable.was_findings import WAS_FINDINGS_DATA
from tests.data.tenable.was_findings import WAS_PLUGIN_ID_1
from tests.data.tenable.was_findings import WAS_PLUGIN_ID_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://cloud.tenable.com"


def _load_assets(neo4j_session, mocker):
    """Helper: sync assets so TenableAsset nodes exist for relationship tests."""
    mocker.patch(
        "cartography.intel.tenable.assets.export_and_download",
        return_value=ASSETS_DATA,
    )
    cartography.intel.tenable.assets.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
    )


def _sync_was_findings(neo4j_session, mocker, data=None):
    """Helper: run WAS findings sync with optional custom data."""
    mocker.patch(
        "cartography.intel.tenable.was_findings.export_and_download",
        return_value=data if data is not None else WAS_FINDINGS_DATA,
    )
    cartography.intel.tenable.was_findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
    )


def test_sync_was_findings(neo4j_session, mocker):
    """Test that WAS findings sync creates TenableWASFinding nodes with correct properties."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    actual_nodes = check_nodes(
        neo4j_session,
        "TenableWASFinding",
        ["id", "severity", "severity_id", "state", "url"],
    )
    assert actual_nodes == {
        (
            WAS_FINDING_ID_1,
            "MEDIUM",
            2,
            "OPEN",
            "https://www.unixtimestamp.com/contact.php",
        ),
        (WAS_FINDING_ID_2, "INFO", 0, "OPEN", "https://example.com/api/health"),
    }


def test_sync_was_findings_cve_fields(neo4j_session, mocker):
    """Test that cve_id and has_cve are set and the CVE label is applied."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    # Finding with CVE
    record = neo4j_session.run(
        "MATCH (f:TenableWASFinding {id: $id}) "
        "RETURN f.cve_id AS cve_id, f.has_cve AS has_cve, f:CVE AS has_cve_label",
        id=WAS_FINDING_ID_1,
    ).single()
    assert record["cve_id"] == "CVE-2015-9251"
    assert record["has_cve"] == "true"
    assert record["has_cve_label"] is True

    # cve_list is stored as a list property
    assert record["cve_id"] == "CVE-2015-9251"
    cve_list_record = neo4j_session.run(
        "MATCH (f:TenableWASFinding {id: $id}) RETURN f.cve_list AS cve_list",
        id=WAS_FINDING_ID_1,
    ).single()
    assert cve_list_record["cve_list"] == ["CVE-2015-9251"]

    # Finding without CVE
    record = neo4j_session.run(
        "MATCH (f:TenableWASFinding {id: $id}) "
        "RETURN f.has_cve AS has_cve, f:CVE AS has_cve_label",
        id=WAS_FINDING_ID_2,
    ).single()
    assert record["has_cve"] == "false"
    assert record["has_cve_label"] is False


def test_sync_was_findings_affects_asset_rel(neo4j_session, mocker):
    """Test that TenableWASFinding-[:AFFECTS]->TenableAsset relationships are created."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    actual_rels = check_rels(
        neo4j_session,
        "TenableWASFinding",
        "id",
        "TenableAsset",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    )
    assert actual_rels == {
        (WAS_FINDING_ID_1, ASSET_ID_1),
        (WAS_FINDING_ID_2, ASSET_ID_2),
    }


def test_sync_was_plugins(neo4j_session, mocker):
    """Test that TenableWASPlugin nodes are created and deduplicated."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    actual_plugins = check_nodes(
        neo4j_session,
        "TenableWASPlugin",
        ["id", "name", "risk_factor", "cvss3_base_score"],
    )
    assert actual_plugins == {
        (
            WAS_PLUGIN_ID_1,
            "jQuery 1.12.4 < 3.0.0 Cross-Site Scripting",
            "MEDIUM",
            6.1,
        ),
        (WAS_PLUGIN_ID_2, "Web Server Version Disclosure", "INFO", None),
    }

    record = neo4j_session.run(
        "MATCH (p:TenableWASPlugin {id: $id}) RETURN p.cve_ids AS cve_ids",
        id=WAS_PLUGIN_ID_1,
    ).single()
    assert record["cve_ids"] == ["CVE-2015-9251"]


def test_sync_was_findings_detected_by_rel(neo4j_session, mocker):
    """Test that TenableWASFinding-[:DETECTED_BY]->TenableWASPlugin relationships are created."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    actual_rels = check_rels(
        neo4j_session,
        "TenableWASFinding",
        "id",
        "TenableWASPlugin",
        "id",
        "DETECTED_BY",
        rel_direction_right=True,
    )
    assert actual_rels == {
        (WAS_FINDING_ID_1, WAS_PLUGIN_ID_1),
        (WAS_FINDING_ID_2, WAS_PLUGIN_ID_2),
    }


def test_sync_was_findings_tenant_resource_rel(neo4j_session, mocker):
    """Test that TenableTenant-[:RESOURCE]->TenableWASFinding relationships are created."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    actual_rels = check_rels(
        neo4j_session,
        "TenableTenant",
        "id",
        "TenableWASFinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert {
        (TENABLE_TENANT_ID, WAS_FINDING_ID_1),
        (TENABLE_TENANT_ID, WAS_FINDING_ID_2),
    } <= actual_rels


def test_sync_was_findings_cleanup(neo4j_session, mocker):
    """Test that stale TenableWASFinding nodes are deleted after sync."""
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (f:TenableWASFinding {id: 'stale-was-finding-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(f)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    result = neo4j_session.run("MATCH (f:TenableWASFinding) RETURN f.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-was-finding-id" not in existing_ids
    assert WAS_FINDING_ID_1 in existing_ids


def test_sync_was_plugins_cleanup(neo4j_session, mocker):
    """Test that stale TenableWASPlugin nodes are deleted after sync."""
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (p:TenableWASPlugin {id: 'stale-was-plugin-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(p)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    result = neo4j_session.run("MATCH (p:TenableWASPlugin) RETURN p.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-was-plugin-id" not in existing_ids
    assert WAS_PLUGIN_ID_1 in existing_ids
    assert WAS_PLUGIN_ID_2 in existing_ids


def test_sync_was_findings_export_filter(neo4j_session, mocker):
    """Every sync sends a last_found filter derived from lookback_days."""
    _load_assets(neo4j_session, mocker)
    mock_export = mocker.patch(
        "cartography.intel.tenable.was_findings.export_and_download",
        return_value=WAS_FINDINGS_DATA,
    )
    lookback_days = 90
    cartography.intel.tenable.was_findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
        lookback_days=lookback_days,
    )

    export_params = mock_export.call_args[0][4]
    assert export_params["filters"]["last_found"] == TEST_UPDATE_TAG - (
        lookback_days * 86400
    )
    assert export_params["filters"]["state"] == ["OPEN", "REOPENED", "FIXED"]
