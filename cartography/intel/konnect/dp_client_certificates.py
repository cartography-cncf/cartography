import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.models.konnect.dp_client_certificate import KonnectDPClientCertificateSchema
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
    Sync Kong Konnect DP Client Certificates.
    
    :param neo4j_session: Neo4j session
    :param api_token: Kong Konnect API token
    :param api_url: Kong Konnect API base URL
    :param update_tag: Update tag
    :param common_job_parameters: Common job parameters
    :return: None
    """
    # Get list of control plane IDs from the graph
    control_plane_ids = get_control_plane_ids(neo4j_session)
    
    all_dp_client_certs = []
    for cp_id in control_plane_ids:
        certs_data = get(api_token, api_url, cp_id)
        transformed_data = transform(certs_data, cp_id)
        all_dp_client_certs.extend(transformed_data)
    
    if all_dp_client_certs:
        load_dp_client_certificates(neo4j_session, all_dp_client_certs, update_tag)
    
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
    Fetch DP client certificates for a specific control plane from Kong Konnect API.
    
    :param api_token: Kong Konnect API token
    :param api_url: Kong Konnect API base URL
    :param control_plane_id: Control plane ID
    :return: List of DP client certificates
    """
    session = Session()
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    
    all_dp_client_certs = []
    url = f"{api_url}/control-planes/{control_plane_id}/dp-client-certificates"
    
    while url:
        logger.info(f"Fetching DP client certificates from {url}")
        response = session.get(url, headers=headers, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if "data" in data:
            all_dp_client_certs.extend(data["data"])
        
        url = data.get("next")
    
    logger.info(f"Fetched {len(all_dp_client_certs)} DP client certificates for control plane {control_plane_id}")
    return all_dp_client_certs


def transform(dp_client_certs: List[Dict[str, Any]], control_plane_id: str) -> List[Dict[str, Any]]:
    """
    Transform DP client certificates data.
    
    :param dp_client_certs: Raw DP client certificates data from API
    :param control_plane_id: Control plane ID
    :return: Transformed DP client certificates data
    """
    transformed = []
    for cert in dp_client_certs:
        # Truncate cert data for storage
        cert_data = cert.get("cert", "")
        cert_preview = cert_data[:100] + "..." if len(cert_data) > 100 else cert_data
        
        transformed.append({
            "id": cert.get("id"),
            "cert": cert_preview,  # Store truncated version
            "created_at": cert.get("created_at"),
            "control_plane_id": control_plane_id,
        })
    
    return transformed


def load_dp_client_certificates(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load DP client certificates into Neo4j.
    
    :param neo4j_session: Neo4j session
    :param data: Transformed DP client certificates data
    :param update_tag: Update tag
    :return: None
    """
    # Group by control plane for loading
    by_control_plane: Dict[str, List[Dict[str, Any]]] = {}
    for cert in data:
        cp_id = cert.pop("control_plane_id")
        if cp_id not in by_control_plane:
            by_control_plane[cp_id] = []
        by_control_plane[cp_id].append(cert)
    
    # Load DP client certificates for each control plane
    for cp_id, certs in by_control_plane.items():
        load(
            neo4j_session,
            KonnectDPClientCertificateSchema(),
            certs,
            lastupdated=update_tag,
            CONTROL_PLANE_ID=cp_id,
        )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Clean up stale DP client certificates.
    
    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters
    :return: None
    """
    query = """
    MATCH (n:KonnectDPClientCertificate)
    WHERE n.lastupdated <> $UPDATE_TAG
    DETACH DELETE n
    """
    neo4j_session.run(query, common_job_parameters)
