"""
Comprehensive integration test for full Proxmox sync.
"""
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox
import cartography.intel.proxmox.cluster
import cartography.intel.proxmox.compute
import cartography.intel.proxmox.storage
from tests.data.proxmox.cluster import MOCK_CLUSTER_DATA
from tests.data.proxmox.cluster import MOCK_NODE_DATA
from tests.data.proxmox.cluster import MOCK_NODE_NETWORK_DATA
from tests.data.proxmox.compute import MOCK_STORAGE_DATA
from tests.data.proxmox.compute import MOCK_VM_CONFIG
from tests.data.proxmox.compute import MOCK_VM_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"

MOCK_NODES = [
    {"node": "node1"},
    {"node": "node2"},
]


@patch.object(cartography.intel.proxmox.cluster, "get_cluster_resources", return_value=MOCK_CLUSTER_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_node_network")
@patch.object(cartography.intel.proxmox.compute, "get_vms_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_containers_for_node")
@patch.object(cartography.intel.proxmox.compute, "get_vm_config")
@patch.object(cartography.intel.proxmox.storage, "get_storage", return_value=MOCK_STORAGE_DATA)
def test_full_proxmox_sync(
    mock_get_storage,
    mock_get_vm_config,
    mock_get_containers,
    mock_get_vms,
    mock_get_node_network,
    mock_get_nodes,
    mock_get_cluster,
    neo4j_session,
):
    """
    Test a complete Proxmox sync including cluster, nodes, VMs, and storage.
    """
    # Arrange
    proxmox = MagicMock()
    proxmox.nodes.get.return_value = MOCK_NODES

    # Setup mocks
    def get_network_side_effect(proxmox_client, node_name):
        return MOCK_NODE_NETWORK_DATA.get(node_name, [])

    def get_vms_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'qemu']

    def get_containers_side_effect(proxmox_client, node_name):
        vms = MOCK_VM_DATA.get(node_name, [])
        return [vm for vm in vms if vm.get('type') == 'lxc']

    def get_config_side_effect(proxmox_client, node, vmid, vm_type):
        return MOCK_VM_CONFIG.get(vmid, {})

    mock_get_node_network.side_effect = get_network_side_effect
    mock_get_vms.side_effect = get_vms_side_effect
    mock_get_containers.side_effect = get_containers_side_effect
    mock_get_vm_config.side_effect = get_config_side_effect

    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act - Sync cluster first
    cartography.intel.proxmox.cluster.sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Add CLUSTER_ID after cluster sync
    common_job_parameters["CLUSTER_ID"] = TEST_CLUSTER_ID

    # Act - Sync compute
    cartography.intel.proxmox.compute.sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Act - Sync storage
    cartography.intel.proxmox.storage.sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Verify the complete graph structure

    # 1. Cluster exists
    expected_cluster = {(TEST_CLUSTER_ID,)}
    assert check_nodes(neo4j_session, "ProxmoxCluster", ["id"]) == expected_cluster

    # 2. Nodes exist and connect to cluster
    expected_nodes = {
        ("node/node1", "node1"),
        ("node/node2", "node2"),
    }
    assert check_nodes(neo4j_session, "ProxmoxNode", ["id", "name"]) == expected_nodes

    # 3. Node network interfaces exist
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNodeNetworkInterface)
        RETURN count(n) as count
        """
    )
    interface_count = result.single()["count"]
    assert interface_count == 4  # From MOCK_NODE_NETWORK_DATA

    # 4. VMs and containers exist
    expected_vms = {
        ("node1/qemu/100", "test-vm-1"),
        ("node1/qemu/101", "test-vm-2"),
        ("node2/lxc/200", "test-container-1"),
    }
    assert check_nodes(neo4j_session, "ProxmoxVM", ["id", "name"]) == expected_vms

    # 5. Disks exist and connect to VMs
    result = neo4j_session.run(
        """
        MATCH (d:ProxmoxDisk)-[:HAS_DISK]->(v:ProxmoxVM)
        RETURN count(d) as count
        """
    )
    disk_count = result.single()["count"]
    assert disk_count == 3  # scsi0 x2 + rootfs x1

    # 6. Network interfaces exist and connect to VMs
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNetworkInterface)-[:HAS_NETWORK_INTERFACE]->(v:ProxmoxVM)
        RETURN count(n) as count
        """
    )
    nic_count = result.single()["count"]
    assert nic_count == 4  # net0 x3 + net1 x1

    # 7. Storage exists and connects to cluster
    expected_storage = {
        (f"{TEST_CLUSTER_ID}/local", "local"),
        (f"{TEST_CLUSTER_ID}/local-lvm", "local-lvm"),
        (f"{TEST_CLUSTER_ID}/nfs-backup", "nfs-backup"),
    }
    assert check_nodes(neo4j_session, "ProxmoxStorage", ["id", "name"]) == expected_storage

    # 8. Verify hierarchical relationships
    # Cluster -> Node -> VM structure
    result = neo4j_session.run(
        """
        MATCH (c:ProxmoxCluster {id: $cluster_id})<-[:RESOURCE]-(n:ProxmoxNode)<-[:RUNS_ON]-(v:ProxmoxVM)
        RETURN count(DISTINCT v) as vm_count
        """,
        cluster_id=TEST_CLUSTER_ID,
    )
    vm_count = result.single()["vm_count"]
    assert vm_count == 3


@patch.object(cartography.intel.proxmox.cluster, "get_cluster_resources", return_value=MOCK_CLUSTER_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_node_network")
def test_cleanup_removes_stale_data(mock_get_node_network, mock_get_nodes, mock_get_cluster, neo4j_session):
    """
    Test that cleanup properly removes nodes that weren't updated in the current sync.
    """
    # Arrange
    proxmox = MagicMock()

    def get_network_side_effect(proxmox_client, node_name):
        return MOCK_NODE_NETWORK_DATA.get(node_name, [])

    mock_get_node_network.side_effect = get_network_side_effect

    # First sync with update_tag 1
    common_job_parameters_1 = {
        "UPDATE_TAG": 1,
    }

    cartography.intel.proxmox.cluster.sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        1,
        common_job_parameters_1,
    )

    # Verify data exists
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNode {id: 'node/node1'})
        RETURN n.lastupdated as lastupdated
        """
    )
    assert result.single()["lastupdated"] == 1

    # Manually add a stale node that won't be in the second sync
    neo4j_session.run(
        """
        MERGE (n:ProxmoxNode {id: 'node/stale-node'})
        SET n.name = 'stale-node',
            n.status = 'offline',
            n.lastupdated = 1
        WITH n
        MATCH (c:ProxmoxCluster {id: $cluster_id})
        MERGE (n)-[r:RESOURCE]->(c)
        SET r.lastupdated = 1
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    # Verify stale node exists
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNode {id: 'node/stale-node'})
        RETURN count(n) as count
        """
    )
    assert result.single()["count"] == 1

    # Second sync with update_tag 2 (will trigger cleanup)
    common_job_parameters_2 = {
        "UPDATE_TAG": 2,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    cartography.intel.proxmox.cluster.sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        2,
        common_job_parameters_2,
    )

    # Verify stale node was removed
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNode {id: 'node/stale-node'})
        RETURN count(n) as count
        """
    )
    assert result.single()["count"] == 0

    # Verify current nodes still exist with updated timestamp
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNode {id: 'node/node1'})
        RETURN n.lastupdated as lastupdated
        """
    )
    assert result.single()["lastupdated"] == 2
