"""
Sync Proxmox storage resources.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any, Dict, List

from cartography.client.core.tx import run_write_query
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions
# ============================================================================

@timeit
def get_storage(proxmox_client) -> List[Dict[str, Any]]:
    """
    Get all storage definitions from Proxmox.

    :param proxmox_client: Proxmox API client
    :return: List of storage dicts
    :raises: Exception if API call fails
    """
    return proxmox_client.storage.get()


@timeit
def get_storage_status(proxmox_client, node_name: str) -> List[Dict[str, Any]]:
    """
    Get storage status for a specific node.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :return: List of storage status dicts
    """
    try:
        return proxmox_client.nodes(node_name).storage.get()
    except Exception as e:
        logger.warning(f"Could not get storage status for node {node_name}: {e}")
        return []


# ============================================================================
# TRANSFORM functions
# ============================================================================

def transform_storage_data(
    storage_list: List[Dict[str, Any]],
    storage_status_map: Dict[str, List[Dict[str, Any]]],
    cluster_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform storage data into standard format.

    :param storage_list: Raw storage definitions from API
    :param storage_status_map: Map of node_name -> storage status list
    :param cluster_id: Parent cluster ID
    :return: List of transformed storage dicts
    """
    transformed_storage = []

    for storage in storage_list:
        # Required fields
        storage_id = storage['storage']

        # Parse content types
        content_types = []
        if storage.get('content'):
            content_types = [c.strip() for c in storage['content'].split(',')]

        # Determine which nodes have access to this storage
        nodes = []
        if storage.get('nodes'):
            # Specific nodes listed
            nodes = [n.strip() for n in storage['nodes'].split(',')]
        else:
            # All nodes have access
            nodes = list(storage_status_map.keys())

        # Try to get size information from status
        total = 0
        used = 0
        available = 0

        for node_name, status_list in storage_status_map.items():
            for status in status_list:
                if status.get('storage') == storage_id:
                    total = max(total, status.get('total', 0))
                    used = max(used, status.get('used', 0))
                    available = max(available, status.get('avail', 0))
                    break

        transformed_storage.append({
            'id': storage_id,
            'name': storage_id,
            'cluster_id': cluster_id,
            'type': storage.get('type'),
            'content_types': content_types,
            'shared': storage.get('shared', 0) == 1,
            'enabled': storage.get('disable', 0) == 0,
            'total': total,
            'used': used,
            'available': available,
            'nodes': nodes,
        })

    return transformed_storage


# ============================================================================
# LOAD functions
# ============================================================================

def load_storage(neo4j_session, storage_list: List[Dict[str, Any]], update_tag: int) -> None:
    """
    Load storage data into Neo4j and create relationships.

    :param neo4j_session: Neo4j session
    :param storage_list: List of transformed storage dicts
    :param update_tag: Sync timestamp
    """
    query = """
    UNWIND $Storage as storage_data
    MERGE (s:ProxmoxStorage{id: storage_data.id})
    ON CREATE SET s.firstseen = timestamp()
    SET s.name = storage_data.name,
        s.cluster_id = storage_data.cluster_id,
        s.type = storage_data.type,
        s.content_types = storage_data.content_types,
        s.shared = storage_data.shared,
        s.enabled = storage_data.enabled,
        s.total = storage_data.total,
        s.used = storage_data.used,
        s.available = storage_data.available,
        s.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        query,
        Storage=storage_list,
        UpdateTag=update_tag,
    )


def load_storage_node_relationships(
    neo4j_session,
    storage_list: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create relationships between storage and nodes.

    :param neo4j_session: Neo4j session
    :param storage_list: List of transformed storage dicts
    :param update_tag: Sync timestamp
    """
    # Flatten storage -> nodes into individual relationships
    relationships = []
    for storage in storage_list:
        for node_name in storage['nodes']:
            relationships.append({
                'storage_id': storage['id'],
                'node_id': node_name,
            })

    if not relationships:
        return

    query = """
    UNWIND $Relationships as rel
    MATCH (s:ProxmoxStorage{id: rel.storage_id})
    MATCH (n:ProxmoxNode{id: rel.node_id})
    MERGE (s)-[r:AVAILABLE_ON]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        query,
        Relationships=relationships,
        UpdateTag=update_tag,
    )


# ============================================================================
# SYNC function
# ============================================================================

@timeit
def sync(
    neo4j_session,
    proxmox_client,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync storage resources.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    """
    logger.info("Syncing Proxmox storage")

    # GET - retrieve data from API
    storage_list = get_storage(proxmox_client)

    # Get storage status from each node for size information
    nodes = proxmox_client.nodes.get()
    storage_status_map = {}

    for node in nodes:
        node_name = node['node']
        storage_status = get_storage_status(proxmox_client, node_name)
        storage_status_map[node_name] = storage_status

    # TRANSFORM - manipulate data for ingestion
    transformed_storage = transform_storage_data(storage_list, storage_status_map, cluster_id)

    # LOAD - ingest to Neo4j
    load_storage(neo4j_session, transformed_storage, update_tag)
    load_storage_node_relationships(neo4j_session, transformed_storage, update_tag)

    logger.info(f"Synced {len(transformed_storage)} storage resources")
