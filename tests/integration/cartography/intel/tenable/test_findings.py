import copy
from typing import Any

import pytest

import cartography.intel.cve_metadata
import cartography.intel.tenable.assets
import cartography.intel.tenable.findings
from cartography.config import Config
from cartography.intel.cve import feed as cve_feed
from cartography.intel.cve_metadata import start_cve_metadata_ingestion
from cartography.intel.cve_metadata.nvd import transform_cves as transform_nvd_cves
from tests.data.cve.feed import GET_CVE_API_DATA
from tests.data.cve_metadata.nvd import GET_NVD_API_DATA
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


@pytest.fixture(autouse=True)
def isolated_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    try:
        yield
    finally:
        neo4j_session.run("MATCH (n) DETACH DELETE n").consume()


@pytest.fixture
def legacy_cve_list_index(neo4j_session):
    """The RANGE index earlier versions declared on TenableFinding.cve_list.

    Cartography never drops an index it no longer declares, so upgraded graphs keep it.
    """
    neo4j_session.run(
        "CREATE INDEX legacy_tenable_finding_cve_list IF NOT EXISTS "
        "FOR (n:TenableFinding) ON (n.cve_list)"
    ).consume()
    # Real graphs have it ONLINE. An oversized write to a POPULATING index can fail
    # at commit and leave the test database needing a restart.
    neo4j_session.run("CALL db.awaitIndexes()").consume()
    try:
        yield
    finally:
        neo4j_session.run(
            "DROP INDEX legacy_tenable_finding_cve_list IF EXISTS"
        ).consume()


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


def _sync_findings(
    neo4j_session,
    mocker,
    data=FINDINGS_DATA,
    tenant_id=TENABLE_TENANT_ID,
    update_tag=TEST_UPDATE_TAG,
):
    """Helper: run findings sync, with the export API returning ``data``."""
    mocker.patch("cartography.intel.tenable.findings.get", return_value=data)
    cartography.intel.tenable.findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        tenant_id,
        update_tag,
        {"UPDATE_TAG": update_tag, "TENABLE_TENANT_ID": tenant_id},
    )


def _load_nvd_records(neo4j_session):
    """Helper: load the NVD fixture through the `cve` module, which MERGEs on (:CVE {id})."""
    # transform_cves() rewrites its input in place, so give it a private copy.
    nvd_data = copy.deepcopy(GET_CVE_API_DATA)
    nvd_feed = cve_feed.transform_cve_feed(nvd_data)
    cve_feed.load_cve_feed(neo4j_session, [nvd_feed], TEST_UPDATE_TAG)
    cve_feed.load_cves(
        neo4j_session,
        cve_feed.transform_cves(nvd_data),
        nvd_feed["FEED_ID"],
        TEST_UPDATE_TAG,
    )


def _finding(finding_id: str, plugin_id: int, cves: list[str]) -> dict[str, Any]:
    """A minimal raw Tenable finding whose plugin names ``cves``."""
    return {
        "finding_id": finding_id,
        "asset": {"uuid": ASSET_ID_1},
        "plugin": {"id": plugin_id, "cve": cves},
    }


def test_sync_findings(neo4j_session, mocker):
    """Test that findings sync creates TenableFinding nodes with correct properties."""
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


def test_sync_findings_keep_the_first_cve_id_and_a_has_cve_flag(neo4j_session, mocker):
    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    assert check_nodes(
        neo4j_session, "TenableFinding", ["id", "cve_id", "has_cve"]
    ) == {
        (FINDING_ID_1, "CVE-2022-21837", "true"),
        (FINDING_ID_2, None, "false"),
        (FINDING_ID_3, None, "false"),
    }


def test_sync_creates_a_cve_node_for_each_cve_a_plugin_names(neo4j_session, mocker):
    # Act
    _sync_findings(neo4j_session, mocker, tenant_id="tenant-a")

    # Assert
    assert check_nodes(neo4j_session, "TenableCve", ["id", "cve_id"]) == {
        ("TNB|tenant-a|CVE-2022-21837", "CVE-2022-21837"),
        ("TNB|tenant-a|CVE-2022-21840", "CVE-2022-21840"),
        ("TNB|tenant-a|CVE-2022-21842", "CVE-2022-21842"),
    }


def test_sync_puts_the_cve_ontology_label_on_cve_nodes_only(neo4j_session, mocker):
    # Act
    _sync_findings(neo4j_session, mocker, tenant_id="tenant-a")

    # Assert: the three TenableCve nodes are the only :CVE nodes; findings are not.
    assert check_nodes(neo4j_session, "CVE", ["id", "_ont_cve_id", "_ont_source"]) == {
        ("TNB|tenant-a|CVE-2022-21837", "CVE-2022-21837", "tenable"),
        ("TNB|tenant-a|CVE-2022-21840", "CVE-2022-21840", "tenable"),
        ("TNB|tenant-a|CVE-2022-21842", "CVE-2022-21842", "tenable"),
    }


def test_sync_links_each_plugin_to_the_cves_it_names(neo4j_session, mocker):
    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    assert check_rels(
        neo4j_session,
        "TenablePlugin",
        "id",
        "TenableCve",
        "cve_id",
        "HAS_CVE",
        rel_direction_right=True,
    ) == {
        (PLUGIN_ID_1, "CVE-2022-21837"),
        (PLUGIN_ID_1, "CVE-2022-21840"),
        (PLUGIN_ID_1, "CVE-2022-21842"),
    }


def test_sync_lets_findings_be_looked_up_by_cve_through_their_plugin(
    neo4j_session, mocker
):
    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert: the lookup documented for users.
    record = neo4j_session.run(
        """
        MATCH (:TenableCve {cve_id: 'CVE-2022-21840'})<-[:HAS_CVE]-(:TenablePlugin)
              <-[:DETECTED_BY]-(f:TenableFinding)
        RETURN f.id AS id
        """
    ).single(strict=True)
    assert record["id"] == FINDING_ID_1


def test_sync_links_a_plugins_cves_once_however_many_hosts_report_it(
    neo4j_session, mocker
):
    # Arrange: one cumulative-update plugin, reported on three hosts.
    cves = ["CVE-2026-0001", "CVE-2026-0002"]
    data = [
        _finding("host-1-finding", plugin_id=1, cves=cves),
        _finding("host-2-finding", plugin_id=1, cves=cves),
        _finding("host-3-finding", plugin_id=1, cves=cves),
    ]

    # Act
    _sync_findings(neo4j_session, mocker, data)

    # Assert
    edge_count = neo4j_session.run(
        "MATCH ()-[r:HAS_CVE]->(:TenableCve) RETURN count(r) AS n"
    ).single(strict=True)["n"]
    assert edge_count == 2


def test_sync_succeeds_with_a_huge_cve_list_on_a_graph_with_the_legacy_index(
    neo4j_session, mocker, legacy_cve_list_index
):
    """Regression test: upgraded graphs must not need the legacy index dropped by hand.

    A RANGE index rejects keys over ~8 KB. 700 CVE IDs encode to more than that, as
    a cumulative OS update's list does.
    """
    # Arrange
    cves = [f"CVE-2026-{n:05d}" for n in range(700)]
    data = [_finding("windows-cumulative-update", plugin_id=1, cves=cves)]

    # Act
    _sync_findings(neo4j_session, mocker, data)

    # Assert
    linked = neo4j_session.run(
        """
        MATCH (:TenableFinding {id: 'windows-cumulative-update'})-[:DETECTED_BY]->
              (:TenablePlugin)-[:HAS_CVE]->(c:TenableCve)
        RETURN count(c) AS n
        """
    ).single(strict=True)["n"]
    assert linked == 700


def test_sync_deletes_cves_no_plugin_names_any_more(neo4j_session, mocker):
    # Arrange
    _sync_findings(
        neo4j_session,
        mocker,
        [_finding("f1", plugin_id=1, cves=["CVE-2026-0001", "CVE-2026-0002"])],
        update_tag=1,
    )

    # Act
    _sync_findings(
        neo4j_session,
        mocker,
        [_finding("f1", plugin_id=1, cves=["CVE-2026-0001"])],
        update_tag=2,
    )

    # Assert
    assert check_nodes(neo4j_session, "TenableCve", ["cve_id"]) == {
        ("CVE-2026-0001",),
    }


def test_sync_unlinks_a_cve_from_a_plugin_that_stops_naming_it(neo4j_session, mocker):
    # Arrange: both plugins name the CVE.
    _sync_findings(
        neo4j_session,
        mocker,
        [
            _finding("f1", plugin_id=1, cves=["CVE-2026-0001"]),
            _finding("f2", plugin_id=2, cves=["CVE-2026-0001"]),
        ],
        update_tag=1,
    )

    # Act: plugin 1 no longer names it.
    _sync_findings(
        neo4j_session,
        mocker,
        [
            _finding("f1", plugin_id=1, cves=[]),
            _finding("f2", plugin_id=2, cves=["CVE-2026-0001"]),
        ],
        update_tag=2,
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "TenablePlugin",
        "id",
        "TenableCve",
        "cve_id",
        "HAS_CVE",
        rel_direction_right=True,
    ) == {(2, "CVE-2026-0001")}


def test_sync_cleanup_for_one_tenant_keeps_another_tenants_cves(neo4j_session, mocker):
    # Arrange: two tenants whose plugins name the same CVE. The plugins differ because
    # plugin ids are not yet tenant-qualified; see the tenant ID note in config.md.
    _sync_findings(
        neo4j_session,
        mocker,
        [_finding("a-f1", plugin_id=1, cves=["CVE-2026-0001"])],
        tenant_id="tenant-a",
        update_tag=1,
    )
    _sync_findings(
        neo4j_session,
        mocker,
        [_finding("b-f1", plugin_id=2, cves=["CVE-2026-0001"])],
        tenant_id="tenant-b",
        update_tag=2,
    )

    # Act: tenant A's host is patched, so tenant A's cleanup retires the CVE.
    _sync_findings(
        neo4j_session,
        mocker,
        [_finding("a-f2", plugin_id=3, cves=[])],
        tenant_id="tenant-a",
        update_tag=3,
    )

    # Assert: tenant B's plugin still reaches the CVE.
    assert check_rels(
        neo4j_session,
        "TenablePlugin",
        "id",
        "TenableCve",
        "cve_id",
        "HAS_CVE",
        rel_direction_right=True,
    ) == {(2, "CVE-2026-0001")}


def test_sync_does_not_let_the_cve_module_adopt_tenable_cve_nodes(
    neo4j_session, mocker
):
    # Arrange: CVE-2023-6493 is in the NVD fixture.
    _sync_findings(
        neo4j_session,
        mocker,
        [_finding("f1", plugin_id=1, cves=["CVE-2023-6493"])],
        tenant_id="tenant-a",
    )

    # Act
    _load_nvd_records(neo4j_session)

    # Assert: two distinct records of the CVE, one per module.
    records = neo4j_session.run(
        """
        MATCH (c:CVE {_ont_cve_id: 'CVE-2023-6493'})
        RETURN c.id AS id, c._ont_source AS source
        ORDER BY id
        """
    ).data()
    assert records == [
        {"id": "CVE-2023-6493", "source": "cve"},
        {"id": "TNB|tenant-a|CVE-2023-6493", "source": "tenable"},
    ]


def test_sync_lets_findings_read_nvd_severity_through_the_ontology(
    neo4j_session, mocker
):
    # Arrange: NVD rates CVE-2023-6493 MEDIUM.
    _load_nvd_records(neo4j_session)

    # Act
    _sync_findings(
        neo4j_session, mocker, [_finding("f1", plugin_id=1, cves=["CVE-2023-6493"])]
    )

    # Assert: the join documented for users.
    record = neo4j_session.run(
        """
        MATCH (f:TenableFinding)-[:DETECTED_BY]->(:TenablePlugin)-[:HAS_CVE]->(t:TenableCve)
        MATCH (n:CVE {_ont_cve_id: t._ont_cve_id, _ont_source: 'cve'})
        RETURN f.id AS finding_id, n._ont_base_severity AS cve_severity
        """
    ).single(strict=True)
    assert (record["finding_id"], record["cve_severity"]) == ("f1", "medium")


def test_cve_metadata_enriches_every_cve_a_plugin_names(neo4j_session, mocker):
    # Arrange: both CVEs are in the NVD metadata fixture. Before TenableCve, only a
    # finding's first CVE carried the :CVE label, so only the first was enriched.
    _sync_findings(
        neo4j_session,
        mocker,
        [_finding("f1", plugin_id=1, cves=["CVE-2023-41782", "CVE-2024-22075"])],
    )
    mocker.patch.object(
        cartography.intel.cve_metadata.nvd,
        "get_and_transform_nvd_cves",
        side_effect=lambda http_session, cve_ids, api_key=None: transform_nvd_cves(
            copy.deepcopy(GET_NVD_API_DATA), cve_ids
        ),
    )
    mocker.patch.object(
        cartography.intel.cve_metadata.epss, "get_epss_scores", return_value={}
    )

    # Act
    start_cve_metadata_ingestion(
        neo4j_session,
        Config(neo4j_uri="bolt://localhost:7687", update_tag=TEST_UPDATE_TAG),
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "CVEMetadata",
        "id",
        "TenableCve",
        "cve_id",
        "ENRICHES",
        rel_direction_right=True,
    ) == {
        ("CVE-2023-41782", "CVE-2023-41782"),
        ("CVE-2024-22075", "CVE-2024-22075"),
    }


def test_sync_strips_the_legacy_cve_label_from_findings(neo4j_session, mocker):
    # Arrange: a finding as releases up to 0.143.0 left it.
    _sync_findings(neo4j_session, mocker)
    neo4j_session.run(
        """
        MATCH (f:TenableFinding {id: $id})
        SET f:CVE, f._ont_source = 'tenable', f._ont_cve_id = 'CVE-2022-21837',
            f.cve_list = ['CVE-2022-21837', 'CVE-2022-21840', 'CVE-2022-21842']
        """,
        id=FINDING_ID_1,
    ).consume()

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    record = neo4j_session.run(
        """
        MATCH (f:TenableFinding {id: $id})
        RETURN f:CVE AS is_cve, f._ont_source AS ont_source, f.cve_list AS cve_list
        """,
        id=FINDING_ID_1,
    ).single(strict=True)
    assert record.data() == {"is_cve": False, "ont_source": None, "cve_list": None}


def test_sync_deletes_finding_to_cve_edges_left_by_earlier_builds(
    neo4j_session, mocker
):
    # Arrange: an edge as builds between #3310 and this change wrote it.
    _sync_findings(neo4j_session, mocker)
    neo4j_session.run(
        """
        MATCH (f:TenableFinding {id: $id}), (c:TenableCve {cve_id: 'CVE-2022-21837'})
        CREATE (f)-[:HAS_CVE]->(c)
        """,
        id=FINDING_ID_1,
    ).consume()

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    edge_count = neo4j_session.run(
        "MATCH (:TenableFinding)-[r:HAS_CVE]->() RETURN count(r) AS n"
    ).single(strict=True)["n"]
    assert edge_count == 0


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


def test_sync_plugins_keep_their_full_cve_list(neo4j_session, mocker):
    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    record = neo4j_session.run(
        "MATCH (p:TenablePlugin {id: $id}) RETURN p.cve_list AS cve_list",
        id=PLUGIN_ID_1,
    ).single(strict=True)
    assert record["cve_list"] == ["CVE-2022-21837", "CVE-2022-21840", "CVE-2022-21842"]


def test_sync_findings_detected_by_rel(neo4j_session, mocker):
    """Test that TenableFinding-[:DETECTED_BY]->TenablePlugin relationships are created."""
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
    """Test that plugins, scans and CVEs have the RESOURCE edge used for cleanup."""
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
    assert check_rels(
        neo4j_session,
        "TenableTenant",
        "id",
        "TenableCve",
        "cve_id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TENABLE_TENANT_ID, "CVE-2022-21837"),
        (TENABLE_TENANT_ID, "CVE-2022-21840"),
        (TENABLE_TENANT_ID, "CVE-2022-21842"),
    }


def test_sync_deletes_findings_absent_from_the_latest_export(neo4j_session, mocker):
    # Arrange
    _sync_findings(neo4j_session, mocker, FINDINGS_DATA, update_tag=1)

    # Act
    _sync_findings(neo4j_session, mocker, [FINDINGS_DATA[0]], update_tag=2)

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

    # Act
    _sync_findings(neo4j_session, mocker)

    # Assert
    result = neo4j_session.run("MATCH (s:TenableScan) RETURN s.id AS id")
    existing_ids = {r["id"] for r in result}
    assert "stale-scan-id" not in existing_ids
    assert SCAN_UUID_1 in existing_ids
    assert SCAN_UUID_2 in existing_ids
