"""
Sync Proxmox clusters and nodes.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any, Dict, List

from cartography.client.core.tx import load
from cartography.models.proxmox.cluster import ProxmoxClusterSchema
from cartography.models.proxmox.cluster import ProxmoxNodeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions - retrieve data from Proxmox API
# Per docs: "should be 'dumb'... raise an exception if not able to complete"
# ============================================================================

@timeit
def get_cluster_status(proxmox_client) -> List[Dict[str, Any]]:
    """
    Get cluster status information.

    :param proxmox_client: Proxmox API client
    :return: Cluster status list
    :raises: Exception if API call fails
    """
    return proxmox_client.cluster.status.get()


@timeit
def get_nodes(proxmox_client) -> List[Dict[str, Any]]:
    """
    Get all nodes in the cluster.

    :param proxmox_client: Proxmox API client
    :return: List of node dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.nodes.get()


@timeit
def get_node_status(proxmox_client, node_name: str) -> Dict[str, Any]:
    """
    Get detailed status for a specific node.

    :param proxmox_client: Proxmox API client
    :param node_name: Name of the node
    :return: Node status dict
    :raises: Exception if API call fails
    """
    return proxmox_client.nodes(node_name).status.get()


@timeit
def get_node_network(proxmox_client, node_name: str) -> List[Dict[str, Any]]:
    """
    Get network interface configuration for a specific node.

    :param proxmox_client: Proxmox API client
    :param node_name: Name of the node
    :return: List of network interface dicts
    :raises: Exception if API call fails
    """
    try:
        return proxmox_client.nodes(node_name).network.get()
    except Exception as e:
        logger.warning(f"Could not get network config for node {node_name}: {e}")
        return []


# ============================================================================
# TRANSFORM functions - manipulate data for graph ingestion
# Per docs: Use data['field'] for required, data.get('field') for optional
# ============================================================================

def transform_cluster_data(
    cluster_status: List[Dict[str, Any]],
    proxmox_host: str,
) -> Dict[str, Any]:
    """
    Transform cluster status data into standard format.

    Per Cartography guidelines:
    - Use data['field'] for required fields (will raise KeyError if missing)
    - Use data.get('field') for optional fields

    :param cluster_status: Raw cluster status from API
    :param proxmox_host: Proxmox hostname for synthetic ID
    :return: Transformed cluster data
    """
    cluster_info = None
    for item in cluster_status:
        # Required field - use direct access
        if item['type'] == 'cluster':
            cluster_info = item
            break

    if not cluster_info:
        # Create synthetic cluster ID from hostname
        cluster_id = proxmox_host.replace('.', '-')
        return {
            'id': cluster_id,
            'name': cluster_id,
            'version': 'unknown',
            'quorate': True,
            'nodes_online': len([i for i in cluster_status if i['type'] == 'node' and i.get('online')]),
        }

    # Per docs: "ID should uniquely identify the node... use API-provided fields for IDs"
    return {
        'id': cluster_info['name'],  # Required field - direct access
        'name': cluster_info['name'],  # Required
        'version': cluster_info.get('version', 'unknown'),  # Optional
        'quorate': cluster_info.get('quorate', True),  # Optional with default
        'nodes_online': len([i for i in cluster_status if i['type'] == 'node' and i.get('online')]),
    }


def transform_node_data(nodes: List[Dict[str, Any]], cluster_id: str) -> List[Dict[str, Any]]:
    """
    Transform node data into standard format.

    :param nodes: Raw node data from API
    :param cluster_id: Parent cluster ID
    :return: List of transformed node dicts
    """
    transformed_nodes = []

    for node in nodes:
        # Use direct access for required fields, .get() for optional
        transformed_nodes.append({
            'id': node['node'],  # Required - API-provided ID
            'name': node['node'],  # Required
            'cluster_id': cluster_id,  # Required
            'hostname': node['node'],  # Use node name as hostname
            'ip': node.get('ip'),  # Optional
            'status': node.get('status', 'unknown'),  # Optional with default
            'uptime': node.get('uptime', 0),  # Optional with default
            'cpu_count': node.get('maxcpu', 0),  # Optional
            'cpu_usage': node.get('cpu', 0.0),  # Optional
            'memory_total': node.get('maxmem', 0),  # Optional
            'memory_used': node.get('mem', 0),  # Optional
            'disk_total': node.get('maxdisk', 0),  # Optional
            'disk_used': node.get('disk', 0),  # Optional
            'level': node.get('level'),  # Optional
        })

    return transformed_nodes


def transform_node_network_data(
    network_interfaces: List[Dict[str, Any]],
    node_name: str,
    cluster_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform node network interface data into standard format.

    :param network_interfaces: Raw network interface data from API
    :param node_name: Node name
    :param cluster_id: Parent cluster ID
    :return: List of transformed network interface dicts
    """
    transformed_interfaces = []

    for iface in network_interfaces:
        # Required field
        iface_name = iface['iface']
        iface_id = f"{node_name}:{iface_name}"

        transformed_interfaces.append({
            'id': iface_id,
            'name': iface_name,
            'node_name': node_name,
            'type': iface.get('type'),  # bridge, bond, eth, vlan, etc.
            'address': iface.get('address'),
            'netmask': iface.get('netmask'),
            'gateway': iface.get('gateway'),
            'address6': iface.get('address6'),
            'netmask6': iface.get('netmask6'),
            'gateway6': iface.get('gateway6'),
            'bridge_ports': iface.get('bridge_ports'),
            'bond_slaves': iface.get('slaves'),  # API uses 'slaves' key
            'active': iface.get('active', False),
            'autostart': iface.get('autostart', False),
            'mtu': iface.get('mtu'),
        })

    return transformed_interfaces


# ============================================================================
# LOAD functions - ingest data to Neo4j using modern data model
# Per AGENTS.md: Use load() function with data model schemas
# ============================================================================

def load_cluster(neo4j_session, cluster_data: Dict[str, Any], update_tag: int) -> None:
    """
    Load cluster data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param cluster_data: Transformed cluster data
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxClusterSchema(),
        [cluster_data],
        lastupdated=update_tag,
    )


def load_nodes(neo4j_session, nodes: List[Dict[str, Any]], cluster_id: str, update_tag: int) -> None:
    """
    Load node data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param nodes: List of transformed node dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxNodeSchema(),
        nodes,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_node_networks(
    neo4j_session,
    network_interfaces: List[Dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load node network interface data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param network_interfaces: List of transformed network interface dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    if not network_interfaces:
        return

    from cartography.models.proxmox.cluster import ProxmoxNodeNetworkInterfaceSchema

    load(
        neo4j_session,
        ProxmoxNodeNetworkInterfaceSchema(),
        network_interfaces,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


# ============================================================================
# SYNC function - orchestrates Get → Transform → Load
# Per docs: "sync should call get, then load, and finally cleanup"
# ============================================================================

@timeit
def sync(
    neo4j_session,
    proxmox_client,
    proxmox_host: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Sync cluster and node data.

    Follows Cartography's Get → Transform → Load pattern.
    Cleanup is handled in separate cleanup job.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param proxmox_host: Proxmox hostname
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    :return: Cluster data dict with cluster_id
    """
    logger.info("Syncing Proxmox cluster and nodes")

    # GET - retrieve data from API
    cluster_status = get_cluster_status(proxmox_client)
    nodes = get_nodes(proxmox_client)

    # TRANSFORM - manipulate data for ingestion
    cluster_data = transform_cluster_data(cluster_status, proxmox_host)
    transformed_nodes = transform_node_data(nodes, cluster_data['id'])

    # LOAD - ingest to Neo4j
    load_cluster(neo4j_session, cluster_data, update_tag)
    load_nodes(neo4j_session, transformed_nodes, cluster_data['id'], update_tag)

    # Sync node network interfaces
    all_node_networks = []
    for node in nodes:
        node_name = node['node']
        # GET network config for this node
        network_interfaces = get_node_network(proxmox_client, node_name)
        # TRANSFORM network data
        transformed_networks = transform_node_network_data(
            network_interfaces,
            node_name,
            cluster_data['id'],
        )
        all_node_networks.extend(transformed_networks)

    # LOAD node network interfaces
    if all_node_networks:
        load_node_networks(neo4j_session, all_node_networks, cluster_data['id'], update_tag)
        logger.info(f"Synced {len(all_node_networks)} network interfaces across {len(nodes)} nodes")

    # CLEANUP is handled in separate cleanup job

    logger.info(f"Synced cluster {cluster_data['id']} with {len(transformed_nodes)} nodes")

    return {'cluster_id': cluster_data['id']}
