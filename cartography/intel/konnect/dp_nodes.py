import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.intel.konnect import control_planes as cp_module
from cartography.models.konnect.dp_node import KonnectDPNodeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_token: str,
    api_url: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync Kong Konnect Data Plane Nodes.
    
    :param neo4j_session: Neo4j session
    :param api_token: Kong Konnect API token
    :param api_url: Kong Konnect API base URL
    :param update_tag: Update tag
    :param common_job_parameters: Common job parameters
    :return: None
    """
    # Get list of control plane IDs from the graph
    control_plane_ids = get_control_plane_ids(neo4j_session)
    
    all_dp_nodes = []
    for cp_id in control_plane_ids:
        dp_nodes_data = get(api_token, api_url, cp_id)
        transformed_data = transform(dp_nodes_data, cp_id)
        all_dp_nodes.extend(transformed_data)
    
    if all_dp_nodes:
        load_dp_nodes(neo4j_session, all_dp_nodes, update_tag)
    
    cleanup(neo4j_session, common_job_parameters)


def get_control_plane_ids(neo4j_session: neo4j.Session) -> List[str]:
    """
    Get list of control plane IDs from the graph.
    
    :param neo4j_session: Neo4j session
    :return: List of control plane IDs
    """
    query = """
    MATCH (cp:KonnectControlPlane)
    RETURN cp.id as id
    """
    result = neo4j_session.run(query)
    return [record["id"] for record in result]


@timeit
def get(api_token: str, api_url: str, control_plane_id: str) -> List[Dict[str, Any]]:
    """
    Fetch DP nodes for a specific control plane from Kong Konnect API.
    
    :param api_token: Kong Konnect API token
    :param api_url: Kong Konnect API base URL
    :param control_plane_id: Control plane ID
    :return: List of DP nodes
    """
    session = Session()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    
    all_dp_nodes = []
    url = f"{api_url}/control-planes/{control_plane_id}/nodes"
    
    while url:
        logger.info(f"Fetching DP nodes from {url}")
        response = session.get(url, headers=headers, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if "data" in data:
            all_dp_nodes.extend(data["data"])
        
        url = data.get("next")
    
    logger.info(f"Fetched {len(all_dp_nodes)} DP nodes for control plane {control_plane_id}")
    return all_dp_nodes


def transform(dp_nodes: List[Dict[str, Any]], control_plane_id: str) -> List[Dict[str, Any]]:
    """
    Transform DP nodes data.
    
    :param dp_nodes: Raw DP nodes data from API
    :param control_plane_id: Control plane ID
    :return: Transformed DP nodes data
    """
    transformed = []
    for node in dp_nodes:
        transformed.append({
            "id": node.get("id"),
            "hostname": node.get("hostname"),
            "version": node.get("version"),
            "status": node.get("status"),
            "last_ping": node.get("last_ping"),
            "config_hash": node.get("config_hash"),
            "created_at": node.get("created_at"),
            "updated_at": node.get("updated_at"),
            "control_plane_id": control_plane_id,
        })
    
    return transformed


def load_dp_nodes(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load DP nodes into Neo4j.
    
    :param neo4j_session: Neo4j session
    :param data: Transformed DP nodes data
    :param update_tag: Update tag
    :return: None
    """
    # Group by control plane for loading
    by_control_plane: Dict[str, List[Dict[str, Any]]] = {}
    for node in data:
        cp_id = node.pop("control_plane_id")
        if cp_id not in by_control_plane:
            by_control_plane[cp_id] = []
        by_control_plane[cp_id].append(node)
    
    # Load nodes for each control plane
    for cp_id, nodes in by_control_plane.items():
        load(
            neo4j_session,
            KonnectDPNodeSchema(),
            nodes,
            lastupdated=update_tag,
            CONTROL_PLANE_ID=cp_id,
        )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Clean up stale DP nodes.
    
    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    :return: None
    """
    query = """
    MATCH (n:KonnectDPNode)
    WHERE n.lastupdated <> $UPDATE_TAG
    DETACH DELETE n
    """
    neo4j_session.run(query, common_job_parameters)
