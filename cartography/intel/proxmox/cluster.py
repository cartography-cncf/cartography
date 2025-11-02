"""
Sync Proxmox clusters and nodes.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any, Dict, List

from cartography.client.core.tx import run_write_query
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


# ============================================================================
# LOAD functions - ingest data to Neo4j
# Per docs: Use MERGE, set lastupdated/firstseen, run queries on indexed fields
# ============================================================================

def load_cluster(neo4j_session, cluster_data: Dict[str, Any], update_tag: int) -> None:
    """
    Load cluster data into Neo4j.

    Per Cartography guidelines:
    - Use MERGE to avoid duplicates
    - Set firstseen on CREATE, lastupdated always
    - Run queries on indexed fields (id is indexed)

    :param neo4j_session: Neo4j session
    :param cluster_data: Transformed cluster data
    :param update_tag: Sync timestamp
    """
    query = """
    MERGE (c:ProxmoxCluster{id: $ClusterId})
    ON CREATE SET c.firstseen = timestamp()
    SET c.name = $Name,
        c.version = $Version,
        c.quorate = $Quorate,
        c.nodes_online = $NodesOnline,
        c.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        query,
        ClusterId=cluster_data['id'],
        Name=cluster_data['name'],
        Version=cluster_data['version'],
        Quorate=cluster_data['quorate'],
        NodesOnline=cluster_data['nodes_online'],
        UpdateTag=update_tag,
    )


def load_nodes(neo4j_session, nodes: List[Dict[str, Any]], cluster_id: str, update_tag: int) -> None:
    """
    Load node data into Neo4j and create relationships to cluster.

    Per Cartography guidelines:
    - Use MERGE for both nodes and relationships
    - Set firstseen/lastupdated on both nodes and relationships
    - Query on indexed fields (id)

    :param neo4j_session: Neo4j session
    :param nodes: List of transformed node dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    query = """
    UNWIND $Nodes as node_data
    MERGE (n:ProxmoxNode{id: node_data.id})
    ON CREATE SET n.firstseen = timestamp()
    SET n.name = node_data.name,
        n.cluster_id = node_data.cluster_id,
        n.ip = node_data.ip,
        n.status = node_data.status,
        n.uptime = node_data.uptime,
        n.cpu_count = node_data.cpu_count,
        n.cpu_usage = node_data.cpu_usage,
        n.memory_total = node_data.memory_total,
        n.memory_used = node_data.memory_used,
        n.disk_total = node_data.disk_total,
        n.disk_used = node_data.disk_used,
        n.lastupdated = $UpdateTag
    WITH n
    MATCH (c:ProxmoxCluster{id: $ClusterId})
    MERGE (c)-[r:CONTAINS_NODE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        query,
        Nodes=nodes,
        ClusterId=cluster_id,
        UpdateTag=update_tag,
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

    # CLEANUP is handled in separate cleanup job

    logger.info(f"Synced cluster {cluster_data['id']} with {len(transformed_nodes)} nodes")

    return {'cluster_id': cluster_data['id']}
