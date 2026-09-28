import cartography.intel.tenable.assets
import cartography.intel.tenable.findings
from tests.data.tenable.assets import ASSET_ID_1
from tests.data.tenable.assets import ASSET_ID_2
from tests.data.tenable.assets import ASSETS_DATA
from tests.data.tenable.assets import TENABLE_TENANT_ID
from tests.data.tenable.findings import FINDING_ID_1
from tests.data.tenable.findings import FINDING_ID_2
from tests.data.tenable.findings import FINDING_ID_3
from tests.data.tenable.findings import FINDINGS_DATA
from tests.data.tenable.findings import PLUGIN_ID_1
from tests.data.tenable.findings import PLUGIN_ID_2
from tests.data.tenable.findings import PLUGIN_ID_3
from tests.data.tenable.findings import SCAN_UUID_1
from tests.data.tenable.findings import SCAN_UUID_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://cloud.tenable.com"


def _load_assets(neo4j_session, mocker):
    """Helper: sync assets so TenableAsset nodes exist for relationship tests."""
    mocker.patch(
        "cartography.intel.tenable.assets.get",
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


def _sync_findings(neo4j_session, mocker, data=None):
    """Helper: run findings sync with optional custom data."""
    mocker.patch(
        "cartography.intel.tenable.findings.get",
        return_value=data if data is not None else FINDINGS_DATA,
    )
    cartography.intel.tenable.findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
    )


def test_sync_findings(neo4j_session, mocker):
    """Test that findings sync creates TenableFinding nodes with correct properties."""
    # Arrange
    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    actual_nodes = check_nodes(
        neo4j_session,
        "TenableFinding",
        ["id", "severity", "severity_id", "state", "port", "protocol", "service"],
    )
    assert actual_nodes == {
        (FINDING_ID_1, "high", 3, "OPEN", 445, "TCP", "cifs"),
        (FINDING_ID_2, "info", 0, "OPEN", 443, "TCP", "www"),
        (FINDING_ID_3, "info", 0, "OPEN", 0, "TCP", None),
    }


def test_sync_findings_cve_fields(neo4j_session, mocker):
    """Test that cve_id and has_cve are set on findings and the CVE label is applied."""
    # Arrange
    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    # Finding with CVEs
    record = neo4j_session.run(
        "MATCH (f:TenableFinding {id: $id}) "
        "RETURN f.cve_id AS cve_id, f.has_cve AS has_cve, "
        "f:CVE AS has_cve_label, f._ont_cve_id AS ontology_cve_id, "
        "f._ont_base_severity AS ontology_severity, "
        "f._ont_vuln_status AS ontology_status, "
        "f._ont_source AS ontology_source",
        id=FINDING_ID_1,
    ).single()
    assert record["cve_id"] == "CVE-2022-21837"
    assert record["has_cve"] == "true"
    assert record["has_cve_label"] is True
    assert record["ontology_cve_id"] == "CVE-2022-21837"
    assert record["ontology_severity"] == "high"
    assert record["ontology_status"] == "open"
    assert record["ontology_source"] == "tenable"

    # Finding without CVEs
    record = neo4j_session.run(
        "MATCH (f:TenableFinding {id: $id}) "
        "RETURN f.has_cve AS has_cve, f:CVE AS has_cve_label",
        id=FINDING_ID_2,
    ).single()
    assert record["has_cve"] == "false"
    assert record["has_cve_label"] is False


def test_sync_findings_affects_asset_rel(neo4j_session, mocker):
    """Test that TenableFinding-[:AFFECTS]->TenableAsset relationships are created."""
    # Arrange
    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    actual_rels = check_rels(
        neo4j_session,
        "TenableFinding",
        "id",
        "TenableAsset",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    )
    assert actual_rels == {
        (FINDING_ID_1, ASSET_ID_1),
        (FINDING_ID_2, ASSET_ID_2),
        (FINDING_ID_3, ASSET_ID_1),
    }


def test_sync_plugins(neo4j_session, mocker):
    """Test that TenablePlugin nodes are created and deduplicated."""
    # Arrange
    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    actual_plugins = check_nodes(
        neo4j_session,
        "TenablePlugin",
        ["id", "name", "family", "risk_factor", "cvss3_base_score"],
    )
    assert actual_plugins == {
        (
            PLUGIN_ID_1,
            "Security Updates for Microsoft SharePoint Server 2016 (January 2022)",
            "Windows : Microsoft Bulletins",
            "high",
            8.8,
        ),
        (
            PLUGIN_ID_2,
            "Missing or Permissive Content-Security-Policy frame-ancestors HTTP Response Header",
            "CGI abuses",
            "info",
            None,
        ),
        (PLUGIN_ID_3, "Nessus Scan Information", "Settings", "none", None),
    }

    # Plugin CVE list lives on TenablePlugin, not on TenableFinding
    record = neo4j_session.run(
        "MATCH (p:TenablePlugin {id: $id}) RETURN p.cve_list AS cve_list",
        id=PLUGIN_ID_1,
    ).single()
    assert set(record["cve_list"]) == {
        "CVE-2022-21837",
        "CVE-2022-21840",
        "CVE-2022-21842",
    }


def test_sync_findings_detected_by_rel(neo4j_session, mocker):
    """Test that TenableFinding-[:DETECTED_BY]->TenablePlugin relationships are created."""
    # Arrange
    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    actual_rels = check_rels(
        neo4j_session,
        "TenableFinding",
        "id",
        "TenablePlugin",
        "id",
        "DETECTED_BY",
        rel_direction_right=True,
    )
    assert actual_rels == {
        (FINDING_ID_1, PLUGIN_ID_1),
        (FINDING_ID_2, PLUGIN_ID_2),
        (FINDING_ID_3, PLUGIN_ID_3),
    }


def test_sync_scans(neo4j_session, mocker):
    """Test that TenableScan nodes are created, deduplicated, and linked to findings."""
    # Arrange
    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    # FINDING_ID_1 and FINDING_ID_3 share SCAN_UUID_1, so only one scan node exists
    actual_scans = check_nodes(neo4j_session, "TenableScan", ["id", "last_scan_target"])
    assert actual_scans == {
        (SCAN_UUID_1, "192.0.2.58"),
        (SCAN_UUID_2, "192.0.2.58"),
    }

    actual_rels = check_rels(
        neo4j_session,
        "TenableFinding",
        "id",
        "TenableScan",
        "id",
        "PART_OF_SCAN",
        rel_direction_right=True,
    )
    assert actual_rels == {
        (FINDING_ID_1, SCAN_UUID_1),
        (FINDING_ID_2, SCAN_UUID_2),
        (FINDING_ID_3, SCAN_UUID_1),
    }


def test_sync_findings_tenant_resource_rel(neo4j_session, mocker):
    """Test that TenableTenant-[:RESOURCE]->TenableFinding relationships are created."""
    # Arrange
    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    actual_rels = check_rels(
        neo4j_session,
        "TenableTenant",
        "id",
        "TenableFinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert actual_rels == {
        (TENABLE_TENANT_ID, FINDING_ID_1),
        (TENABLE_TENANT_ID, FINDING_ID_2),
        (TENABLE_TENANT_ID, FINDING_ID_3),
    }


def test_sync_finding_subresources_have_tenant_ownership(neo4j_session, mocker):
    """Test that plugins and scans have the RESOURCE edge used for cleanup."""
    # Arrange
    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    assert check_rels(
        neo4j_session,
        "TenableTenant",
        "id",
        "TenablePlugin",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TENABLE_TENANT_ID, PLUGIN_ID_1),
        (TENABLE_TENANT_ID, PLUGIN_ID_2),
        (TENABLE_TENANT_ID, PLUGIN_ID_3),
    }
    assert check_rels(
        neo4j_session,
        "TenableTenant",
        "id",
        "TenableScan",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TENABLE_TENANT_ID, SCAN_UUID_1),
        (TENABLE_TENANT_ID, SCAN_UUID_2),
    }


def test_sync_findings_cleanup(neo4j_session, mocker):
    """Test that stale TenableFinding nodes are deleted after sync."""
    # Arrange
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (f:TenableFinding {id: 'stale-finding-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(f)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker, data=[FINDINGS_DATA[0]])

    # Assert
    result = neo4j_session.run("MATCH (f:TenableFinding) RETURN f.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-finding-id" not in existing_ids
    assert FINDING_ID_1 in existing_ids


def test_sync_findings_cleanup_across_update_tags(neo4j_session, mocker):
    """Test that a second complete sync removes findings absent from the new export."""
    # Arrange
    _load_assets(neo4j_session, mocker)
    first_update_tag = TEST_UPDATE_TAG
    second_update_tag = TEST_UPDATE_TAG + 1
    mocker.patch(
        "cartography.intel.tenable.findings.get",
        side_effect=[FINDINGS_DATA, [FINDINGS_DATA[0]]],
    )

    # Act
    cartography.intel.tenable.findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        first_update_tag,
        {
            "UPDATE_TAG": first_update_tag,
            "TENABLE_TENANT_ID": TENABLE_TENANT_ID,
        },
    )
    cartography.intel.tenable.findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        second_update_tag,
        {
            "UPDATE_TAG": second_update_tag,
            "TENABLE_TENANT_ID": TENABLE_TENANT_ID,
        },
    )

    # Assert
    assert check_nodes(neo4j_session, "TenableFinding", ["id"]) == {(FINDING_ID_1,)}


def test_sync_plugins_cleanup(neo4j_session, mocker):
    """Test that stale TenablePlugin nodes are deleted after sync."""
    # Arrange
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (p:TenablePlugin {id: 'stale-plugin-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(p)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    result = neo4j_session.run("MATCH (p:TenablePlugin) RETURN p.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-plugin-id" not in existing_ids
    assert PLUGIN_ID_1 in existing_ids
    assert PLUGIN_ID_2 in existing_ids
    assert PLUGIN_ID_3 in existing_ids


def test_sync_scans_cleanup(neo4j_session, mocker):
    """Test that stale TenableScan nodes are deleted after sync."""
    # Arrange
    old_update_tag = TEST_UPDATE_TAG - 1000
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: $update_tag})
        CREATE (s:TenableScan {id: 'stale-scan-id', lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE]->(s)
        """,
        tenant_id=TENABLE_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
        old_tag=old_update_tag,
    )

    _load_assets(neo4j_session, mocker)

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    result = neo4j_session.run("MATCH (s:TenableScan) RETURN s.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-scan-id" not in existing_ids
    assert SCAN_UUID_1 in existing_ids
    assert SCAN_UUID_2 in existing_ids
