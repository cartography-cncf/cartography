"""
Integration tests for Proxmox cluster module.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.cluster
from cartography.intel.proxmox.cluster import sync as cluster_sync
from tests.data.proxmox.cluster import MOCK_CLUSTER_CONFIG
from tests.data.proxmox.cluster import MOCK_CLUSTER_DATA
from tests.data.proxmox.cluster import MOCK_CLUSTER_OPTIONS
from tests.data.proxmox.cluster import MOCK_NODE_DATA
from tests.data.proxmox.cluster import MOCK_NODE_NETWORK_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_status",
    return_value=MOCK_CLUSTER_DATA,
)
@patch.object(
    cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_options",
    return_value=MOCK_CLUSTER_OPTIONS,
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_config",
    return_value=MOCK_CLUSTER_CONFIG,
)
def test_sync_cluster_and_nodes(
    mock_get_config, mock_get_options, mock_get_nodes, mock_get_cluster, neo4j_session
):
    """
    Test that cluster and node sync correctly creates proper nodes and relationships.
    """
    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
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
    assert (
        check_nodes(neo4j_session, "ProxmoxCluster", ["id"]) == expected_cluster_nodes
    )

    # Assert - Check node nodes
    expected_node_nodes = {
        ("node1", "node1", "online"),
        ("node2", "node2", "online"),
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxNode", ["id", "name", "status"])
        == expected_node_nodes
    )

    # Assert - Check node->cluster relationships
    expected_rels = {
        ("node1", TEST_CLUSTER_ID),
        ("node2", TEST_CLUSTER_ID),
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


@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_status",
    return_value=MOCK_CLUSTER_DATA,
)
@patch.object(
    cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_options",
    return_value=MOCK_CLUSTER_OPTIONS,
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_config",
    return_value=MOCK_CLUSTER_CONFIG,
)
@patch.object(cartography.intel.proxmox.cluster, "get_node_network")
def test_sync_node_network_interfaces(
    mock_get_node_network,
    mock_get_config,
    mock_get_options,
    mock_get_nodes,
    mock_get_cluster,
    neo4j_session,
):
    """
    Test that node network interfaces sync correctly.
    """
    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
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
        ("node1:vmbr0", "vmbr0", "bridge"),
        ("node1:enp0s31f6", "enp0s31f6", "eth"),
        ("node2:vmbr0", "vmbr0", "bridge"),
    }
    assert (
        check_nodes(
            neo4j_session, "ProxmoxNodeNetworkInterface", ["id", "name", "type"]
        )
        == expected_interface_nodes
    )

    # Assert - Check interface->node relationships
    expected_rels = {
        ("node1:vmbr0", "node1"),
        ("node1:enp0s31f6", "node1"),
        ("node2:vmbr0", "node2"),
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
        ("node1:vmbr0", TEST_CLUSTER_ID),
        ("node1:enp0s31f6", TEST_CLUSTER_ID),
        ("node2:vmbr0", TEST_CLUSTER_ID),
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


@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_status",
    return_value=MOCK_CLUSTER_DATA,
)
@patch.object(
    cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_options",
    return_value=MOCK_CLUSTER_OPTIONS,
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_config",
    return_value=MOCK_CLUSTER_CONFIG,
)
@patch.object(cartography.intel.proxmox.cluster, "get_node_network")
def test_network_interface_properties(
    mock_get_node_network,
    mock_get_config,
    mock_get_options,
    mock_get_nodes,
    mock_get_cluster,
    neo4j_session,
):
    """
    Test that network interface properties are correctly stored.
    """
    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
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

    # Assert - Check specific properties of the bridge interface
    # Note: The mock data has two entries for vmbr0 (IPv4 and IPv6), and the transform function
    # processes them sequentially with the same ID, so the last one wins.
    # In this case, the IPv6 entry is last, so those properties will be stored.
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNodeNetworkInterface {id: 'node1:vmbr0'})
        RETURN n.address, n.gateway, n.netmask, n.address6, n.gateway6, n.netmask6
        """
    )
    data = result.single()
    assert data is not None
    # The last entry in mock data for vmbr0 is the IPv6 one, so it overwrites the IPv4 data
    assert data["n.address"] == "2001:db8::10"  # From second vmbr0 entry
    assert data["n.address6"] == "2001:db8::10"
    assert data["n.gateway6"] == "2001:db8::1"
    assert data["n.netmask6"] == 64


@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_status",
    return_value=MOCK_CLUSTER_DATA,
)
@patch.object(
    cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_options",
    return_value=MOCK_CLUSTER_OPTIONS,
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_config",
    return_value=MOCK_CLUSTER_CONFIG,
)
def test_cluster_enhanced_metadata(
    mock_get_config, mock_get_options, mock_get_nodes, mock_get_cluster, neo4j_session
):
    """
    Test that enhanced cluster metadata fields are correctly captured.
    """
    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Act
    cluster_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check enhanced cluster properties
    result = neo4j_session.run(
        """
        MATCH (c:ProxmoxCluster {id: $cluster_id})
        RETURN c.nodes_total, c.nodes_online, c.cluster_id, c.version, c.quorate
        """,
        cluster_id=TEST_CLUSTER_ID,
    )
    data = result.single()
    assert data is not None
    assert data["c.nodes_total"] == 3  # From MOCK_CLUSTER_DATA
    assert data["c.nodes_online"] == 2  # Two nodes with online=1
    assert data["c.cluster_id"] == "cluster/test-cluster"  # From MOCK_CLUSTER_DATA
    assert data["c.version"] == "8.1.3"
    assert data["c.quorate"] is True


@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_status",
    return_value=MOCK_CLUSTER_DATA,
)
@patch.object(
    cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_options",
    return_value=MOCK_CLUSTER_OPTIONS,
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_config",
    return_value=MOCK_CLUSTER_CONFIG,
)
def test_node_enhanced_metadata(
    mock_get_config, mock_get_options, mock_get_nodes, mock_get_cluster, neo4j_session
):
    """
    Test that enhanced node metadata fields are correctly captured.
    """
    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Act
    cluster_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check enhanced node properties for node1
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNode {id: 'node1'})
        RETURN n.kversion, n.loadavg, n.wait, n.swap_total, n.swap_used,
               n.swap_free, n.pveversion, n.cpuinfo, n.idle
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.kversion"] == "Linux 6.2.16-3-pve"
    assert data["n.loadavg"] == "0.15,0.25,0.3"  # Comma-separated from array
    assert data["n.wait"] == 0.02
    assert data["n.swap_total"] == 8589934592
    assert data["n.swap_used"] == 1073741824
    assert data["n.swap_free"] == 8589934592 - 1073741824  # Calculated
    assert data["n.pveversion"] == "pve-manager/8.1.3/b46aac3b42da5d15"
    assert data["n.cpuinfo"] == "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz"
    assert data["n.idle"] == 0.73


@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_status",
    return_value=MOCK_CLUSTER_DATA,
)
@patch.object(
    cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_options",
    return_value=MOCK_CLUSTER_OPTIONS,
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_config",
    return_value=MOCK_CLUSTER_CONFIG,
)
@patch.object(cartography.intel.proxmox.cluster, "get_node_network")
def test_network_interface_enhanced_metadata(
    mock_get_node_network,
    mock_get_config,
    mock_get_options,
    mock_get_nodes,
    mock_get_cluster,
    neo4j_session,
):
    """
    Test that enhanced network interface metadata fields are correctly captured.
    """
    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
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

    # Assert - Check enhanced network interface properties
    result = neo4j_session.run(
        """
        MATCH (n:ProxmoxNodeNetworkInterface {id: 'node1:vmbr0'})
        RETURN n.mtu, n.comments, n.cidr, n.cidr6, n.method, n.method6
        """
    )
    data = result.single()
    assert data is not None
    assert data["n.mtu"] == 1500
    assert data["n.comments"] == "Main bridge interface"
    # These should come from one of the vmbr0 entries
    assert data["n.cidr"] is not None or data["n.cidr6"] is not None
    assert data["n.method"] is not None or data["n.method6"] is not None


@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_status",
    return_value=MOCK_CLUSTER_DATA,
)
@patch.object(
    cartography.intel.proxmox.cluster, "get_nodes", return_value=MOCK_NODE_DATA
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_options",
    return_value=MOCK_CLUSTER_OPTIONS,
)
@patch.object(
    cartography.intel.proxmox.cluster,
    "get_cluster_config",
    return_value=MOCK_CLUSTER_CONFIG,
)
def test_cluster_configuration_metadata(
    mock_get_config, mock_get_options, mock_get_nodes, mock_get_cluster, neo4j_session
):
    """
    Test that cluster configuration metadata from options and config endpoints is captured correctly.
    """
    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Act
    cluster_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check cluster options (migration, console, email, etc.)
    result = neo4j_session.run(
        """
        MATCH (cluster:ProxmoxCluster {id: $cluster_id})
        RETURN cluster.migration_type as migration_type,
               cluster.migration_network as migration_network,
               cluster.migration_bandwidth_limit as migration_bandwidth_limit,
               cluster.console as console,
               cluster.email_from as email_from,
               cluster.http_proxy as http_proxy,
               cluster.keyboard as keyboard,
               cluster.language as language,
               cluster.mac_prefix as mac_prefix,
               cluster.max_workers as max_workers,
               cluster.next_id_lower as next_id_lower,
               cluster.next_id_upper as next_id_upper
        """,
        cluster_id=TEST_CLUSTER_ID,
    )
    data = result.single()
    assert data is not None

    # Migration settings
    assert data["migration_type"] == "secure"
    assert data["migration_network"] == "192.168.1.0/24"
    assert data["migration_bandwidth_limit"] == 102400

    # Console and UI settings
    assert data["console"] == "html5"
    assert data["keyboard"] == "en-us"
    assert data["language"] == "en"

    # Email and proxy (from MOCK_CLUSTER_OPTIONS)
    assert data["email_from"] == "admin@proxmox.local"
    assert data["http_proxy"] == "http://proxy.example.com:8080"

    # Cluster resource management
    assert data["mac_prefix"] == "BC:24:11"
    assert data["max_workers"] == 4
    assert data["next_id_lower"] == 100
    assert data["next_id_upper"] == 999999999

    # Assert - Check corosync/totem configuration
    result = neo4j_session.run(
        """
        MATCH (cluster:ProxmoxCluster {id: $cluster_id})
        RETURN cluster.totem_cluster_name as totem_cluster_name,
               cluster.totem_config_version as totem_config_version,
               cluster.totem_interface as totem_interface,
               cluster.totem_ip_version as totem_ip_version,
               cluster.totem_secauth as totem_secauth,
               cluster.totem_version as totem_version
        """,
        cluster_id=TEST_CLUSTER_ID,
    )
    data = result.single()
    assert data is not None

    # Corosync/Totem configuration (from MOCK_CLUSTER_CONFIG)
    assert data["totem_cluster_name"] == "test-cluster"
    assert data["totem_config_version"] == 3
    assert data["totem_interface"] == "vmbr0"
    assert data["totem_ip_version"] == "ipv4"
    assert data["totem_secauth"] == "on"
    assert data["totem_version"] == 2
