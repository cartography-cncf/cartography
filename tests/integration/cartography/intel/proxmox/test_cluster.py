"""
Integration tests for Proxmox cluster module.
"""
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.cluster
from cartography.intel.proxmox.cluster import sync as cluster_sync
from tests.data.proxmox.cluster import MOCK_CLUSTER_DATA
from tests.data.proxmox.cluster import MOCK_NODE_DATA
from tests.data.proxmox.cluster import MOCK_NODE_NETWORK_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(cartography.intel.proxmox.cluster, "get_cluster_resources", return_value=MOCK_CLUSTER_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA)
def test_sync_cluster_and_nodes(mock_get_nodes, mock_get_cluster, neo4j_session):
    """
    Test that cluster and node sync correctly creates proper nodes and relationships.
    """
    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    cluster_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check cluster node
    expected_cluster_nodes = {
        (TEST_CLUSTER_ID,),
    }
    assert check_nodes(neo4j_session, "ProxmoxCluster", ["id"]) == expected_cluster_nodes

    # Assert - Check node nodes
    expected_node_nodes = {
        ("node/node1", "node1", "online"),
        ("node/node2", "node2", "online"),
    }
    assert check_nodes(neo4j_session, "ProxmoxNode", ["id", "name", "status"]) == expected_node_nodes

    # Assert - Check node->cluster relationships
    expected_rels = {
        ("node/node1", TEST_CLUSTER_ID),
        ("node/node2", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxNode",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )


@patch.object(cartography.intel.proxmox.cluster, "get_cluster_resources", return_value=MOCK_CLUSTER_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_node_network")
def test_sync_node_network_interfaces(mock_get_node_network, mock_get_nodes, mock_get_cluster, neo4j_session):
    """
    Test that node network interfaces sync correctly.
    """
    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Mock network data for each node
    def get_network_side_effect(proxmox_client, node_name):
        return MOCK_NODE_NETWORK_DATA.get(node_name, [])

    mock_get_node_network.side_effect = get_network_side_effect

    # Act
    cluster_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check network interface nodes (sampling a few key ones)
    expected_interface_nodes = {
        ("node/node1:vmbr0:inet", "vmbr0", "bridge"),
        ("node/node1:vmbr0:inet6", "vmbr0", "bridge"),
        ("node/node1:enp0s31f6:inet", "enp0s31f6", "eth"),
        ("node/node2:vmbr0:inet", "vmbr0", "bridge"),
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxNodeNetworkInterface", ["id", "name", "type"]) == expected_interface_nodes
    )

    # Assert - Check interface->node relationships
    expected_rels = {
        ("node/node1:vmbr0:inet", "node/node1"),
        ("node/node1:vmbr0:inet6", "node/node1"),
        ("node/node1:enp0s31f6:inet", "node/node1"),
        ("node/node2:vmbr0:inet", "node/node2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxNodeNetworkInterface",
            "id",
            "ProxmoxNode",
            "id",
            "HAS_NETWORK_INTERFACE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert - Check interface->cluster relationships
    expected_cluster_rels = {
        ("node/node1:vmbr0:inet", TEST_CLUSTER_ID),
        ("node/node1:vmbr0:inet6", TEST_CLUSTER_ID),
        ("node/node1:enp0s31f6:inet", TEST_CLUSTER_ID),
        ("node/node2:vmbr0:inet", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxNodeNetworkInterface",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_cluster_rels
    )


@patch.object(cartography.intel.proxmox.cluster, "get_cluster_resources", return_value=MOCK_CLUSTER_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA)
@patch.object(cartography.intel.proxmox.cluster, "get_node_network")
def test_network_interface_properties(mock_get_node_network, mock_get_nodes, mock_get_cluster, neo4j_session):
    """
    Test that network interface properties are correctly stored.
    """
    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    def get_network_side_effect(proxmox_client, node_name):
        return MOCK_NODE_NETWORK_DATA.get(node_name, [])

    mock_get_node_network.side_effect = get_network_side_effect

    # Act
    cluster_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check specific properties of the IPv4 bridge interface
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNodeNetworkInterface {id: 'node/node1:vmbr0:inet'})
        RETURN n.ipv4_address, n.ipv4_gateway, n.ipv4_netmask, n.bridge_ports
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.ipv4_address"] == "192.168.1.10"
    assert data["n.ipv4_gateway"] == "192.168.1.1"
    assert data["n.ipv4_netmask"] == "255.255.255.0"
    assert data["n.bridge_ports"] == "enp0s31f6"

    # Assert - Check specific properties of the IPv6 interface
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNodeNetworkInterface {id: 'node/node1:vmbr0:inet6'})
        RETURN n.ipv6_address, n.ipv6_gateway, n.ipv6_netmask
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.ipv6_address"] == "2001:db8::10"
    assert data["n.ipv6_gateway"] == "2001:db8::1"
    assert data["n.ipv6_netmask"] == 64
