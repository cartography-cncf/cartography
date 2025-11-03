"""
Integration tests for Proxmox HA sync.
"""
from typing import Any
from unittest.mock import patch

import cartography.intel.proxmox.ha
from tests.data.proxmox.ha import MOCK_HA_GROUP_DATA
from tests.data.proxmox.ha import MOCK_HA_RESOURCE_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(cartography.intel.proxmox.ha, "get_ha_groups", return_value=MOCK_HA_GROUP_DATA)
@patch.object(cartography.intel.proxmox.ha, "get_ha_resources", return_value=MOCK_HA_RESOURCE_DATA)
def test_sync_ha(mock_get_resources, mock_get_groups, neo4j_session):
    """
    Test that HA groups and resources sync correctly.
    """
    # Arrange
    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Create cluster first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id,
            c.lastupdated = $update_tag
        """,
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create VMs for relationship tests
    neo4j_session.run(
        """
        MERGE (v1:ProxmoxVM {vmid: 100})
        SET v1.id = 'node1:100', v1.name = 'test-vm-1', v1.lastupdated = $update_tag
        MERGE (v2:ProxmoxVM {vmid: 101})
        SET v2.id = 'node1:101', v2.name = 'test-vm-2', v2.lastupdated = $update_tag
        MERGE (v3:ProxmoxVM {vmid: 200})
        SET v3.id = 'node2:200', v3.name = 'test-container-1', v3.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.proxmox.ha.sync(
        neo4j_session,
        None,  # proxmox_client mocked
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - HA groups exist
    expected_groups = {
        ("ha-group-1", "node1,node2"),
        ("ha-group-2", "node2"),
    }
    assert check_nodes(neo4j_session, "ProxmoxHAGroup", ["id", "nodes"]) == expected_groups

    # Assert - HA resources exist
    expected_resources = {
        ("vm:100", "started"),
        ("ct:200", "started"),
        ("vm:101", "stopped"),
    }
    assert check_nodes(neo4j_session, "ProxmoxHAResource", ["id", "state"]) == expected_resources

    # Assert - HA group to cluster relationships
    expected_group_rels = {
        ("ha-group-1", TEST_CLUSTER_ID),
        ("ha-group-2", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxHAGroup",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_group_rels
    )

    # Assert - HA resource to cluster relationships
    expected_resource_rels = {
        ("vm:100", TEST_CLUSTER_ID),
        ("ct:200", TEST_CLUSTER_ID),
        ("vm:101", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxHAResource",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_resource_rels
    )

    # Assert - HA resource to HA group relationships
    expected_ha_group_rels = {
        ("vm:100", "ha-group-1"),
        ("ct:200", "ha-group-1"),
        ("vm:101", "ha-group-2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxHAResource",
            "id",
            "ProxmoxHAGroup",
            "id",
            "MEMBER_OF_HA_GROUP",
            rel_direction_right=True,
        )
        == expected_ha_group_rels
    )

    # Assert - HA resource to VM relationships
    result = neo4j_session.run(
        """
        MATCH (ha:ProxmoxHAResource)-[:PROTECTS]->(v:ProxmoxVM)
        RETURN ha.id as ha_id, v.vmid as vmid
        ORDER BY ha_id
        """
    )
    ha_vm_rels = [(r["ha_id"], r["vmid"]) for r in result]
    assert ha_vm_rels == [
        ("ct:200", 200),
        ("vm:100", 100),
        ("vm:101", 101),
    ]

    # Assert - HA group properties
    result = neo4j_session.run(
        """
        MATCH (g:ProxmoxHAGroup {id: 'ha-group-2'})
        RETURN g.restricted as restricted, g.nofailback as nofailback
        """
    )
    record = result.single()
    assert record["restricted"] is True
    assert record["nofailback"] is True
