import copy

import pytest
import requests

import cartography.intel.tenable.assets
import cartography.intel.tenable.findings
import cartography.intel.tenable.was_findings
from tests.data.tenable.assets import ASSET_ID_1
from tests.data.tenable.assets import ASSET_ID_2
from tests.data.tenable.assets import ASSETS_DATA
from tests.data.tenable.assets import TENABLE_TENANT_ID
from tests.data.tenable.findings import FINDINGS_DATA
from tests.data.tenable.was_findings import WAS_FINDING_ID_1
from tests.data.tenable.was_findings import WAS_FINDING_ID_2
from tests.data.tenable.was_findings import WAS_FINDINGS_DATA
from tests.data.tenable.was_findings import WAS_PLUGIN_ID_1
from tests.data.tenable.was_findings import WAS_PLUGIN_ID_2
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://cloud.tenable.com"
WAS_CVE_NODE_ID = f"TNB|{TENABLE_TENANT_ID}|CVE-2015-9251"


@pytest.fixture(autouse=True)
def isolated_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    try:
        yield
    finally:
        neo4j_session.run("MATCH (n) DETACH DELETE n").consume()


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


def _sync_was_findings(neo4j_session, mocker, data=None, update_tag=TEST_UPDATE_TAG):
    """Helper: run WAS findings sync with optional custom data and update tag."""
    mocker.patch(
        "cartography.intel.tenable.was_findings.export_and_download",
        return_value=data if data is not None else WAS_FINDINGS_DATA,
    )
    cartography.intel.tenable.was_findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        update_tag,
        {"UPDATE_TAG": update_tag, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
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


def test_sync_was_findings_asset_fqdn(neo4j_session, mocker):
    """The scanned application's FQDN is stored, lowercased, on the finding."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    assert check_nodes(neo4j_session, "TenableWASFinding", ["id", "asset_fqdn"]) == {
        (WAS_FINDING_ID_1, "www.unixtimestamp.com"),
        (WAS_FINDING_ID_2, "example.com"),
    }


def test_sync_was_findings_input_fields(neo4j_session, mocker):
    """Per-input findings on one URL stay separate and keep their input and method."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    assert check_nodes(
        neo4j_session, "TenableWASFinding", ["id", "input_name", "http_method"]
    ) == {
        (WAS_FINDING_ID_1, "q", "GET"),
        (WAS_FINDING_ID_2, None, None),
    }


def test_sync_was_findings_have_no_cve_properties_or_label(neo4j_session, mocker):
    """CVEs are reached through the plugin; findings carry no CVE label or fields."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    record = neo4j_session.run(
        "MATCH (f:TenableWASFinding {id: $id}) "
        "RETURN f:CVE AS has_cve_label, f.cve_id AS cve_id, "
        "f.cve_list AS cve_list, f.has_cve AS has_cve",
        id=WAS_FINDING_ID_1,
    ).single()
    assert record["has_cve_label"] is False
    assert record["cve_id"] is None
    assert record["cve_list"] is None
    assert record["has_cve"] is None
    assert check_nodes(neo4j_session, "CVE", ["id"]) == {(WAS_CVE_NODE_ID,)}


def test_sync_was_plugin_has_cve_rel(neo4j_session, mocker):
    """TenableWASPlugin-[:HAS_CVE]->TenableCve, with the CVE ontology label."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    assert check_nodes(neo4j_session, "TenableCve", ["id", "cve_id"]) == {
        (WAS_CVE_NODE_ID, "CVE-2015-9251"),
    }
    assert check_rels(
        neo4j_session,
        "TenableWASPlugin",
        "id",
        "TenableCve",
        "id",
        "HAS_CVE",
        rel_direction_right=True,
    ) == {(WAS_PLUGIN_ID_1, WAS_CVE_NODE_ID)}
    assert check_rels(
        neo4j_session,
        "TenableTenant",
        "id",
        "TenableCve",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {(TENABLE_TENANT_ID, WAS_CVE_NODE_ID)}
    # A finding reaches its CVE through the plugin that detected it.
    record = neo4j_session.run(
        """
        MATCH (:TenableWASFinding {id: $id})-[:DETECTED_BY]->(:TenableWASPlugin)
              -[:HAS_CVE]->(c:TenableCve:CVE)
        RETURN c.cve_id AS cve_id
        """,
        id=WAS_FINDING_ID_1,
    ).single()
    assert record["cve_id"] == "CVE-2015-9251"


def test_was_and_vm_plugins_share_one_cve_node(neo4j_session, mocker):
    """A CVE named by both a VM plugin and a WAS plugin is a single TenableCve node."""
    shared_cve = FINDINGS_DATA[0]["plugin"]["cve"][0]
    was_data = copy.deepcopy(WAS_FINDINGS_DATA)
    was_data[0]["plugin"]["cve"] = [shared_cve]
    _load_assets(neo4j_session, mocker)
    mocker.patch(
        "cartography.intel.tenable.findings.export_and_download",
        return_value=FINDINGS_DATA,
    )
    cartography.intel.tenable.findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
    )
    _sync_was_findings(neo4j_session, mocker, data=was_data)

    shared_node_id = f"TNB|{TENABLE_TENANT_ID}|{shared_cve}"
    assert (
        len(
            neo4j_session.run(
                "MATCH (c:TenableCve {id: $id}) RETURN c", id=shared_node_id
            ).data()
        )
        == 1
    )
    record = neo4j_session.run(
        """
        MATCH (c:TenableCve {id: $id})
        OPTIONAL MATCH (c)<-[:HAS_CVE]-(vm:TenablePlugin)
        OPTIONAL MATCH (c)<-[:HAS_CVE]-(was:TenableWASPlugin)
        RETURN count(DISTINCT vm) AS vm_plugins, count(DISTINCT was) AS was_plugins
        """,
        id=shared_node_id,
    ).single()
    assert record["vm_plugins"] >= 1
    assert record["was_plugins"] == 1


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
        "MATCH (p:TenableWASPlugin {id: $id}) RETURN p.cve_list AS cve_list",
        id=WAS_PLUGIN_ID_1,
    ).single()
    assert record["cve_list"] == ["CVE-2015-9251"]


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
    # A JSON boolean: Tenable documents include_unlicensed as a boolean.
    assert export_params["include_unlicensed"] is True


def test_sync_was_findings_unresolved_critical_high_query(neo4j_session, mocker):
    """Unresolved Critical/High findings can be listed per application."""
    data = copy.deepcopy(WAS_FINDINGS_DATA)
    for finding, (severity, state) in zip(
        data, [("CRITICAL", "OPEN"), ("HIGH", "FIXED")], strict=True
    ):
        finding["severity"] = severity
        finding["state"] = state
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker, data=data)

    rows = neo4j_session.run(
        """
        MATCH (f:TenableWASFinding)
        WHERE f.state IN ['OPEN', 'REOPENED'] AND f.severity IN ['CRITICAL', 'HIGH']
        RETURN f.asset_fqdn AS app, f.id AS id
        """
    ).data()
    assert {(r["app"], r["id"]) for r in rows} == {
        ("www.unixtimestamp.com", WAS_FINDING_ID_1)
    }


def test_second_sync_updates_in_place_and_removes_vanished(neo4j_session, mocker):
    """The same finding id is updated, not duplicated; gone findings/CVEs are removed."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    second_tag = TEST_UPDATE_TAG + 1
    # Finding 1 is now FIXED; finding 2 has left the export; its plugin has no CVE.
    second_run = [copy.deepcopy(WAS_FINDINGS_DATA[0])]
    second_run[0]["state"] = "FIXED"
    second_run[0]["last_found"] = "2024-04-01T00:00:00Z"
    second_run[0]["plugin"]["cve"] = []
    _sync_was_findings(neo4j_session, mocker, data=second_run, update_tag=second_tag)

    assert check_nodes(
        neo4j_session,
        "TenableWASFinding",
        ["id", "state", "first_found", "last_found"],
    ) == {
        (
            WAS_FINDING_ID_1,
            "FIXED",
            "2024-02-01T16:08:41Z",
            "2024-04-01T00:00:00Z",
        )
    }
    assert check_nodes(neo4j_session, "TenableWASPlugin", ["id"]) == {
        (WAS_PLUGIN_ID_1,)
    }
    # The CVE the plugin no longer names is gone, and so is its edge.
    assert check_nodes(neo4j_session, "TenableCve", ["id"]) == set()


def test_was_finding_without_matching_asset_is_kept_without_affects(
    neo4j_session, mocker
):
    """No TenableAsset for the asset uuid: the finding loads, with no AFFECTS edge."""
    data = copy.deepcopy(WAS_FINDINGS_DATA)
    data[1]["asset"]["uuid"] = "00000000-0000-4000-8000-000000000000"
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker, data=data)

    assert check_rels(
        neo4j_session,
        "TenableWASFinding",
        "id",
        "TenableAsset",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {(WAS_FINDING_ID_1, ASSET_ID_1)}
    assert (WAS_FINDING_ID_2,) in check_nodes(
        neo4j_session, "TenableWASFinding", ["id"]
    )


def _forbidden_response() -> requests.HTTPError:
    response = requests.Response()
    response.status_code = 403
    return requests.HTTPError(response=response)


def test_was_403_skips_sync_and_keeps_existing_data(neo4j_session, mocker):
    """A key without WAS permission must not wipe data from an earlier run."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    mocker.patch(
        "cartography.intel.tenable.was_findings.export_and_download",
        side_effect=_forbidden_response(),
    )
    second_tag = TEST_UPDATE_TAG + 1
    cartography.intel.tenable.was_findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        second_tag,
        {"UPDATE_TAG": second_tag, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
    )

    assert check_nodes(neo4j_session, "TenableWASFinding", ["id"]) == {
        (WAS_FINDING_ID_1,),
        (WAS_FINDING_ID_2,),
    }


def test_was_non_403_http_error_propagates_and_keeps_data(neo4j_session, mocker):
    """Other HTTP errors (for example a 404 from a wrong path) are not swallowed here."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    response = requests.Response()
    response.status_code = 404
    mocker.patch(
        "cartography.intel.tenable.was_findings.export_and_download",
        side_effect=requests.HTTPError(response=response),
    )
    second_tag = TEST_UPDATE_TAG + 1
    with pytest.raises(requests.HTTPError):
        cartography.intel.tenable.was_findings.sync(
            neo4j_session,
            mocker.MagicMock(),
            TEST_BASE_URL,
            TENABLE_TENANT_ID,
            second_tag,
            {"UPDATE_TAG": second_tag, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
        )

    assert check_nodes(neo4j_session, "TenableWASFinding", ["id"]) == {
        (WAS_FINDING_ID_1,),
        (WAS_FINDING_ID_2,),
    }


def test_repeated_vm_then_was_runs_keep_was_only_cves(neo4j_session, mocker):
    """
    The VM sync's TenableCve cleanup runs before the WAS sync in every run. The keep-alive
    stops it removing a CVE that only WAS plugins name, so the CVE and its edge are never
    absent, not even between the two syncs.
    """
    _load_assets(neo4j_session, mocker)
    mocker.patch(
        "cartography.intel.tenable.findings.export_and_download",
        return_value=FINDINGS_DATA,
    )

    def run_both(update_tag):
        params = {"UPDATE_TAG": update_tag, "TENABLE_TENANT_ID": TENABLE_TENANT_ID}
        cartography.intel.tenable.was_findings.keep_cves_named_by_was_plugins(
            neo4j_session, TENABLE_TENANT_ID, update_tag
        )
        cartography.intel.tenable.findings.sync(
            neo4j_session,
            mocker.MagicMock(),
            TEST_BASE_URL,
            TENABLE_TENANT_ID,
            update_tag,
            params,
        )
        _sync_was_findings(neo4j_session, mocker, update_tag=update_tag)

    run_both(TEST_UPDATE_TAG)
    run_both(TEST_UPDATE_TAG + 1)

    assert check_rels(
        neo4j_session,
        "TenableWASPlugin",
        "id",
        "TenableCve",
        "id",
        "HAS_CVE",
        rel_direction_right=True,
    ) == {(WAS_PLUGIN_ID_1, WAS_CVE_NODE_ID)}
    # And the VM data is intact.
    assert (
        len(
            neo4j_session.run(
                "MATCH (:TenablePlugin)-[:HAS_CVE]->(:TenableCve) RETURN 1"
            ).data()
        )
        > 0
    )


def _run_vm_findings_sync(neo4j_session, mocker, update_tag, data=None):
    mocker.patch(
        "cartography.intel.tenable.findings.export_and_download",
        return_value=FINDINGS_DATA if data is None else data,
    )
    cartography.intel.tenable.findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        update_tag,
        {"UPDATE_TAG": update_tag, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
    )


def test_was_only_cve_survives_vm_cleanup_when_was_sync_is_skipped(
    neo4j_session, mocker
):
    """
    A 403 on the WAS export skips the WAS sync. The CVE that only WAS plugins name, and
    its HAS_CVE edge, must still be there after the VM sync's cleanup.
    """
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    second_tag = TEST_UPDATE_TAG + 1
    cartography.intel.tenable.was_findings.keep_cves_named_by_was_plugins(
        neo4j_session, TENABLE_TENANT_ID, second_tag
    )
    _run_vm_findings_sync(neo4j_session, mocker, second_tag)
    mocker.patch(
        "cartography.intel.tenable.was_findings.export_and_download",
        side_effect=_forbidden_response(),
    )
    cartography.intel.tenable.was_findings.sync(
        neo4j_session,
        mocker.MagicMock(),
        TEST_BASE_URL,
        TENABLE_TENANT_ID,
        second_tag,
        {"UPDATE_TAG": second_tag, "TENABLE_TENANT_ID": TENABLE_TENANT_ID},
    )

    assert check_nodes(neo4j_session, "TenableCve", ["id"]) >= {(WAS_CVE_NODE_ID,)}
    assert check_rels(
        neo4j_session,
        "TenableWASPlugin",
        "id",
        "TenableCve",
        "id",
        "HAS_CVE",
        rel_direction_right=True,
    ) == {(WAS_PLUGIN_ID_1, WAS_CVE_NODE_ID)}
    # The tenant edge matters too: without it the CVE falls outside the tenant-scoped
    # cleanup and would never be removed.
    assert check_rels(
        neo4j_session,
        "TenableTenant",
        "id",
        "TenableCve",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) >= {(TENABLE_TENANT_ID, WAS_CVE_NODE_ID)}


def test_cve_kept_while_was_is_skipped_is_removed_once_no_plugin_names_it(
    neo4j_session, mocker
):
    """The keep-alive must not make a CVE immortal: once nothing names it, it goes."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)

    # Run 2: WAS skipped. The CVE is kept, with its tenant edge.
    tag2 = TEST_UPDATE_TAG + 1
    cartography.intel.tenable.was_findings.keep_cves_named_by_was_plugins(
        neo4j_session, TENABLE_TENANT_ID, tag2
    )
    _run_vm_findings_sync(neo4j_session, mocker, tag2)
    assert (WAS_CVE_NODE_ID,) in check_nodes(neo4j_session, "TenableCve", ["id"])

    # Run 3: WAS succeeds and no longer names the CVE.
    tag3 = TEST_UPDATE_TAG + 2
    cartography.intel.tenable.was_findings.keep_cves_named_by_was_plugins(
        neo4j_session, TENABLE_TENANT_ID, tag3
    )
    _run_vm_findings_sync(neo4j_session, mocker, tag3)
    without_cve = copy.deepcopy(WAS_FINDINGS_DATA)
    for finding in without_cve:
        finding["plugin"]["cve"] = []
    _sync_was_findings(neo4j_session, mocker, data=without_cve, update_tag=tag3)

    # Run 4: nothing names it, so neither the keep-alive nor any sync touches it.
    tag4 = TEST_UPDATE_TAG + 3
    cartography.intel.tenable.was_findings.keep_cves_named_by_was_plugins(
        neo4j_session, TENABLE_TENANT_ID, tag4
    )
    _run_vm_findings_sync(neo4j_session, mocker, tag4)

    assert (WAS_CVE_NODE_ID,) not in check_nodes(neo4j_session, "TenableCve", ["id"])


def test_vm_cleanup_still_removes_cves_no_plugin_names(neo4j_session, mocker):
    """The keep-alive only protects CVEs named by a WAS plugin."""
    _load_assets(neo4j_session, mocker)
    _sync_was_findings(neo4j_session, mocker)
    stale_cve_id = f"TNB|{TENABLE_TENANT_ID}|CVE-1999-0001"
    neo4j_session.run(
        """
        MATCH (t:TenableTenant {id: $tenant_id})
        CREATE (c:TenableCve:CVE {id: $cve_id, cve_id: 'CVE-1999-0001',
                                   lastupdated: $old_tag})
        CREATE (t)-[:RESOURCE {lastupdated: $old_tag}]->(c)
        """,
        tenant_id=TENABLE_TENANT_ID,
        cve_id=stale_cve_id,
        old_tag=TEST_UPDATE_TAG,
    )

    second_tag = TEST_UPDATE_TAG + 1
    cartography.intel.tenable.was_findings.keep_cves_named_by_was_plugins(
        neo4j_session, TENABLE_TENANT_ID, second_tag
    )
    _run_vm_findings_sync(neo4j_session, mocker, second_tag)

    remaining = {row[0] for row in check_nodes(neo4j_session, "TenableCve", ["id"])}
    assert stale_cve_id not in remaining
    assert WAS_CVE_NODE_ID in remaining


def test_keep_cves_named_by_was_plugins_without_was_data_is_a_noop(neo4j_session):
    """Tenants that never ran WAS have no WAS plugins; nothing is touched."""
    neo4j_session.run(
        """
        CREATE (t:TenableTenant {id: $tenant_id, lastupdated: 1})
        CREATE (c:TenableCve {id: 'TNB|x|CVE-1', cve_id: 'CVE-1', lastupdated: 1})
        CREATE (t)-[:RESOURCE]->(c)
        """,
        tenant_id=TENABLE_TENANT_ID,
    )

    cartography.intel.tenable.was_findings.keep_cves_named_by_was_plugins(
        neo4j_session, TENABLE_TENANT_ID, TEST_UPDATE_TAG
    )

    record = neo4j_session.run(
        "MATCH (c:TenableCve {id: 'TNB|x|CVE-1'}) RETURN c.lastupdated AS lu"
    ).single()
    assert record["lu"] == 1
