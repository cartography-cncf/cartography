import json
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.models.konnect.service import KonnectServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)


def get_control_plane_ids(neo4j_session: neo4j.Session) -> List[str]:
    """
    Retrieve all Control Plane IDs from the graph.
    """
    query = """
    MATCH (cp:KonnectControlPlane)
    RETURN cp.id as id
    """
    results = neo4j_session.run(query)
    return [record['id'] for record in results]


def get(api_token: str, api_url: str, control_plane_id: str) -> List[Dict[str, Any]]:
    """
    Fetch services for a specific control plane from Kong Konnect API.
    Handles pagination.
    """
    services = []
    url = f"{api_url}/control-planes/{control_plane_id}/core-entities/services"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    session = Session()
    offset = None

    logger.info(f"Fetching services from {url}")

    while True:
        params = {"size": 100}
        if offset:
            params["offset"] = offset

        response = session.get(url, headers=headers, params=params, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        services.extend(data.get("data", []))

        # Check for pagination
        next_offset = data.get("offset")
        if next_offset:
            offset = next_offset
        else:
            break

    logger.info(f"Fetched {len(services)} services for control plane {control_plane_id}")
    return services


def transform(services_data: List[Dict[str, Any]], control_plane_id: str) -> List[Dict[str, Any]]:
    """
    Transform services data to match the KonnectServiceSchema.
    """
    for service in services_data:
        service['control_plane_id'] = control_plane_id
        # Convert lists to JSON strings for Neo4j storage
        if 'ca_certificates' in service and service['ca_certificates']:
            service['ca_certificates'] = json.dumps(service['ca_certificates'])
        if 'tags' in service and service['tags']:
            service['tags'] = json.dumps(service['tags'])
    return services_data


def load_services(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    control_plane_id: str,
    update_tag: int,
) -> None:
    """
    Load services into Neo4j using the KonnectServiceSchema.
    """
    load(
        neo4j_session,
        KonnectServiceSchema(),
        data,
        lastupdated=update_tag,
        CONTROL_PLANE_ID=control_plane_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Remove stale services from the graph.
    """
    query = """
    MATCH (s:KonnectService)
    WHERE s.lastupdated <> $UPDATE_TAG
    DETACH DELETE s
    """
    neo4j_session.run(query, UPDATE_TAG=common_job_parameters['UPDATE_TAG'])


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_token: str,
    api_url: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync Kong Konnect Services for all control planes.
    """
    control_plane_ids = get_control_plane_ids(neo4j_session)

    for cp_id in control_plane_ids:
        services_data = get(api_token, api_url, cp_id)
        transformed_data = transform(services_data, cp_id)
        load_services(neo4j_session, transformed_data, cp_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
