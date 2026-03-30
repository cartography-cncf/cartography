"""
Integration tests for ontology devices module
"""

from unittest.mock import patch

import cartography.intel.ontology.devices
import tests.data.snipeit.tenants
from tests.integration.cartography.intel.snipeit.test_snipeit_assets import (
    _ensure_local_neo4j_has_test_snipeit_assets,
)
from tests.integration.cartography.intel.snipeit.test_snipeit_users import (
    _ensure_local_neo4j_has_test_snipeit_users,
)
from tests.integration.cartography.intel.tailscale.test_devices import (
    _ensure_local_neo4j_has_test_devices as _ensure_local_neo4j_has_test_tailscale_devices,
)
from tests.integration.cartography.intel.tailscale.test_users import (
    _ensure_local_neo4j_has_test_users as _ensure_local_neo4j_has_test_tailscale_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG = "simpson.corp"
TEST_SNIPEIT_TENANT_ID = tests.data.snipeit.tenants.TENANTS["simpson_corp"]["id"]


def test_sync_with_empty_source_list(neo4j_session):
    """Test sync behavior with empty source of truth list"""
    # Arrange
    _ensure_local_neo4j_has_test_snipeit_assets(neo4j_session)
    _ensure_local_neo4j_has_test_tailscale_devices(neo4j_session)

    # Act
    cartography.intel.ontology.devices.sync(
        neo4j_session, [], TEST_UPDATE_TAG, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )

    device_count = neo4j_session.run(
        "MATCH (d:Device) RETURN count(d) as count"
    ).single()["count"]
    assert device_count == 6


@patch.object(
    cartography.intel.ontology.devices,
    "get_source_nodes_from_graph",
    return_value=[
        {
            "hostname": "donut-mac",
            "serial_number": "SIMP-MAC-HOMER-01",
            "model": "Macbook Pro",
        },
        {
            "hostname": "itchy-windows",
            "serial_number": "SIMP-WIN-MARGE-01",
            "model": "Dell XPS 15",
        },
        {
            "hostname": "bluemarge-linux",
            "serial_number": "SIMP-LINUX-MARGE-017",
            "model": "ThinkPad X1 Carbon Gen 11",
        },
        {
            "hostname": "anonymous-pixel",
            "serial_number": "HACK-PIXEL-01",
            "os": "android",
        },
    ],
)
def test_load_ontology_devices_integration(_mock_get_source_nodes, neo4j_session):
    """Test end-to-end loading of ontology devices"""

    # Arrange
    _ensure_local_neo4j_has_test_snipeit_assets(neo4j_session)
    _ensure_local_neo4j_has_test_tailscale_devices(neo4j_session)

    # Act
    cartography.intel.ontology.devices.sync(
        neo4j_session, ["snipeit"], TEST_UPDATE_TAG, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )

    # Assert - Check that Device nodes were created
    expected_devices = {
        ("donut-mac", "SIMP-MAC-HOMER-01", "Macbook Pro"),
        ("itchy-windows", "SIMP-WIN-MARGE-01", "Dell XPS 15"),
        ("bluemarge-linux", "SIMP-LINUX-MARGE-017", "ThinkPad X1 Carbon Gen 11"),
        ("anonymous-pixel", "HACK-PIXEL-01", None),
        (
            "homer-iphone",
            "SIMP-IOS-HOMER-01",
            "Iphone 15 Pro",
        ),
        (
            "slingshot-galaxy",
            "SIMP-ANDROID-MARGE-01",
            "Samsung Galaxy S23",
        ),
    }

    actual_devices = check_nodes(
        neo4j_session, "Device", ["hostname", "serial_number", "model"]
    )
    assert actual_devices == expected_devices

    # Assert - Check that Device nodes have Ontology label
    devices_with_ontology_label = neo4j_session.run(
        "MATCH (d:Device:Ontology) RETURN count(d) as count"
    ).single()["count"]
    assert devices_with_ontology_label == 6

    # Assert - Check that relationships to SnipeitAsset nodes were created
    expected_rels = {
        ("donut-mac", "donut-mac"),
        ("itchy-windows", "itchy-windows"),
        ("bluemarge-linux", "bluemarge-linux"),
        ("homer-iphone", "homer-iphone"),
        ("slingshot-galaxy", "slingshot-galaxy"),
    }
    actual_rels = check_rels(
        neo4j_session,
        "Device",
        "hostname",
        "SnipeitAsset",
        "name",
        "OBSERVED_AS",
        rel_direction_right=True,
    )
    assert actual_rels == expected_rels

    # Assert - Check that relationships to TailscaleDevice nodes were created
    expected_rels = {
        ("bluemarge-linux", "bluemarge-linux"),
        ("itchy-windows", "itchy-windows"),
        ("donut-mac", "donut-mac"),
        ("anonymous-pixel", "anonymous-pixel"),
    }
    actual_rels = check_rels(
        neo4j_session,
        "Device",
        "hostname",
        "TailscaleDevice",
        "hostname",
        "OBSERVED_AS",
        rel_direction_right=True,
    )
    assert actual_rels == expected_rels


def test_load_ontology_devices_relationships(neo4j_session):
    """Test loading ontology devices relationships"""

    # Arrange
    _ensure_local_neo4j_has_test_snipeit_users(neo4j_session)
    _ensure_local_neo4j_has_test_tailscale_users(neo4j_session)
    _ensure_local_neo4j_has_test_snipeit_assets(neo4j_session)
    _ensure_local_neo4j_has_test_tailscale_devices(neo4j_session)
    # Manually map ussers
    neo4j_session.run(
        """
        MATCH (a:SnipeitUser)
        MERGE (a)<-[:HAS_ACCOUNT]-(u:User {id: a.email})
        SET u.email = a.email
        """
    )
    neo4j_session.run(
        """
        MATCH (a:TailscaleUser)
        MERGE (a)<-[:HAS_ACCOUNT]-(u:User {id: a.email})
        SET u.email = a.email
        """
    )

    # Act
    cartography.intel.ontology.devices.sync(
        neo4j_session, ["snipeit"], TEST_UPDATE_TAG, {"UPDATE_TAG": TEST_UPDATE_TAG}
    )

    # Assert - Check that User and Devices nodes in ontology are linked correctly
    expected_rels = {
        ("hjsimpson@simpson.corp", "donut-mac"),
        ("mbsimpson@simpson.corp", "itchy-windows"),
        ("hjsimpson@simpson.corp", "anonymous-pixel"),
        ("hjsimpson@simpson.corp", "homer-iphone"),
        ("mbsimpson@simpson.corp", "bluemarge-linux"),
        ("mbsimpson@simpson.corp", "slingshot-galaxy"),
    }
    assert (
        check_rels(
            neo4j_session,
            "User",
            "email",
            "Device",
            "hostname",
            "OWNS",
            rel_direction_right=True,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.ontology.devices,
    "get_source_nodes_from_graph",
    return_value=[
        {
            "hostname": "donut-mac",
            "serial_number": "UNMATCHED-SERIAL-01",
            "model": "Macbook Pro",
        },
    ],
)
def test_hostname_matchlink_falls_back_when_serial_match_is_missing(
    _mock_get_source_nodes,
    neo4j_session,
):
    """Hostname matching should still be considered for serial-capable providers."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    neo4j_session.run(
        """
        MERGE (asset:SnipeitAsset {id: 'asset-1'})
        SET asset.name = 'donut-mac',
            asset.serial = 'SIMP-MAC-HOMER-01',
            asset.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    cartography.intel.ontology.devices.load_devices(
        neo4j_session,
        _mock_get_source_nodes.return_value,
        TEST_UPDATE_TAG,
    )

    assert cartography.intel.ontology.devices._should_run_hostname_matchlink(
        neo4j_session,
        "SnipeitAsset",
        "name",
        TEST_UPDATE_TAG,
    )


def test_link_ontology_devices_ignores_stale_observed_as_relationships(neo4j_session):
    """OWNS derivation should only use Device observations from the current run."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (u:User {id: 'user-1'})
        SET u.email = 'hjsimpson@simpson.corp'
        MERGE (su:SnipeitUser {id: 'snipeit-user-1'})
        SET su.email = 'hjsimpson@simpson.corp'
        MERGE (u)-[:HAS_ACCOUNT]->(su)

        MERGE (asset:SnipeitAsset {id: 'asset-1'})
        SET asset.name = 'donut-mac',
            asset.serial = 'SIMP-MAC-HOMER-01'
        MERGE (su)-[:HAS_CHECKED_OUT]->(asset)

        MERGE (d:Device {id: 'device-1'})
        SET d.serial_number = 'SIMP-MAC-HOMER-01',
            d.hostname = 'donut-mac',
            d.lastupdated = $current_tag
        MERGE (d)-[obs:OBSERVED_AS]->(asset)
        SET obs.lastupdated = $stale_tag
        """,
        current_tag=TEST_UPDATE_TAG,
        stale_tag=TEST_UPDATE_TAG - 1,
    )

    cartography.intel.ontology.devices.link_ontology_nodes(
        neo4j_session,
        "devices",
        TEST_UPDATE_TAG,
    )

    assert (
        neo4j_session.run(
            """
            MATCH (:User {id: 'user-1'})-[r:OWNS]->(:Device {id: 'device-1'})
            RETURN count(r) AS count
            """
        ).single()["count"]
        == 0
    )


def test_cleanup_removes_stale_user_owns_device_relationships(neo4j_session):
    """Device cleanup should delete stale ontology-derived User-OWNS-Device edges."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    stale_tag = TEST_UPDATE_TAG - 1

    neo4j_session.run(
        """
        MERGE (u:User:Ontology {id: 'hjsimpson@simpson.corp'})
        SET u.email = 'hjsimpson@simpson.corp',
            u.lastupdated = $update_tag

        MERGE (d:Device:Ontology {id: 'SIMP-MAC-HOMER-01'})
        SET d.serial_number = 'SIMP-MAC-HOMER-01',
            d.hostname = 'donut-mac',
            d.lastupdated = $update_tag

        MERGE (asset:SnipeitAsset {id: 'asset-1'})
        SET asset.name = 'donut-mac',
            asset.serial = 'SIMP-MAC-HOMER-01'

        MERGE (u)-[owns:OWNS]->(d)
        SET owns.lastupdated = $stale_tag

        MERGE (d)-[obs:OBSERVED_AS]->(asset)
        SET obs.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
        stale_tag=stale_tag,
    )

    cartography.intel.ontology.devices.cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    stale_owns_count = neo4j_session.run(
        """
        MATCH (:User {id: 'hjsimpson@simpson.corp'})-[r:OWNS]->(:Device {id: 'SIMP-MAC-HOMER-01'})
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert stale_owns_count == 0

    fresh_observed_as_count = neo4j_session.run(
        """
        MATCH (:Device {id: 'SIMP-MAC-HOMER-01'})-[r:OBSERVED_AS]->(:SnipeitAsset {id: 'asset-1'})
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert fresh_observed_as_count == 1
