import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.models.konnect.control_plane import KonnectControlPlaneSchema
from cartography.models.konnect.organization import KonnectOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_token: str,
    api_url: str,
    org_id: Optional[str],
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> List[str]:
    """
    Sync Kong Konnect Control Planes.
    
    :param neo4j_session: Neo4j session
    :param api_token: Kong Konnect API token
    :param api_url: Kong Konnect API base URL
    :param org_id: Kong Konnect organization ID
    :param update_tag: Update tag
    :param common_job_parameters: Common job parameters
    :return: List of control plane IDs
    """
    control_planes_data = get(api_token, api_url)
    transformed_data = transform(control_planes_data, org_id)
    load_control_planes(neo4j_session, transformed_data, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    
    # Return list of control plane IDs for use by other modules
    return [cp["id"] for cp in transformed_data]


@timeit
def get(api_token: str, api_url: str) -> List[Dict[str, Any]]:
    """
    Fetch control planes from Kong Konnect API.
    
    :param api_token: Kong Konnect API token
    :param api_url: Kong Konnect API base URL
    :return: List of control planes
    """
    session = Session()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    
    # Fetch control planes (paginated)
    all_control_planes = []
    url = f"{api_url}/control-planes"
    
    while url:
        logger.info(f"Fetching control planes from {url}")
        response = session.get(url, headers=headers, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # Add control planes from this page
        if "data" in data:
            all_control_planes.extend(data["data"])
        
        # Check for next page
        url = data.get("next")
    
    logger.info(f"Fetched {len(all_control_planes)} control planes")
    return all_control_planes


def transform(control_planes: List[Dict[str, Any]], org_id: Optional[str]) -> List[Dict[str, Any]]:
    """
    Transform control planes data.
    
    :param control_planes: Raw control planes data from API
    :param org_id: Organization ID
    :return: Transformed control planes data
    """
    # Use org_id if provided, otherwise use a default value
    effective_org_id = org_id or "default"
    
    transformed = []
    for cp in control_planes:
        transformed.append({
            "id": cp.get("id"),
            "name": cp.get("name"),
            "description": cp.get("description"),
            "created_at": cp.get("created_at"),
            "updated_at": cp.get("updated_at"),
        })
    
    return transformed


def load_control_planes(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org_id: Optional[str],
    update_tag: int,
) -> None:
    """
    Load control planes into Neo4j.
    
    :param neo4j_session: Neo4j session
    :param data: Transformed control planes data
    :param org_id: Organization ID
    :param update_tag: Update tag
    :return: None
    """
    # Use org_id if provided, otherwise use a default value
    effective_org_id = org_id or "default"
    
    # Load organization node first
    load(
        neo4j_session,
        KonnectOrganizationSchema(),
        [{"id": effective_org_id, "name": effective_org_id}],
        lastupdated=update_tag,
    )
    
    # Load control planes
    load(
        neo4j_session,
        KonnectControlPlaneSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=effective_org_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Clean up stale control planes.
    
    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    :return: None
    """
    run_cleanup_job(
        "konnect_control_plane_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


def run_cleanup_job(
    cleanup_job_name: str,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Run a cleanup job to remove stale nodes.
    
    :param cleanup_job_name: Name of the cleanup job
    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    :return: None
    """
    # Simple cleanup query to remove nodes not updated in this run
    query = """
    MATCH (n:KonnectControlPlane)
    WHERE n.lastupdated <> $UPDATE_TAG
    DETACH DELETE n
    """
    neo4j_session.run(query, common_job_parameters)
