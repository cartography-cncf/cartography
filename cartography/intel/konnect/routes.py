import json
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.models.konnect.route import KonnectRouteSchema
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
    Fetch routes for a specific control plane from Kong Konnect API.
    Handles pagination.
    """
    routes = []
    url = f"{api_url}/control-planes/{control_plane_id}/core-entities/routes"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    session = Session()
    offset = None

    logger.info(f"Fetching routes from {url}")

    while True:
        params = {"size": 100}
        if offset:
            params["offset"] = offset

        response = session.get(url, headers=headers, params=params, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        routes.extend(data.get("data", []))

        # Check for pagination
        next_offset = data.get("offset")
        if next_offset:
            offset = next_offset
        else:
            break

    logger.info(f"Fetched {len(routes)} routes for control plane {control_plane_id}")
    return routes


def transform(routes_data: List[Dict[str, Any]], control_plane_id: str) -> List[Dict[str, Any]]:
    """
    Transform routes data to match the KonnectRouteSchema.
    """
    for route in routes_data:
        route['control_plane_id'] = control_plane_id

        # Extract service ID if present
        if 'service' in route and route['service'] and isinstance(route['service'], dict):
            route['service_id'] = route['service'].get('id')
        else:
            route['service_id'] = None

        # Convert lists to JSON strings for Neo4j storage
        for field in ['protocols', 'methods', 'hosts', 'paths', 'snis', 'sources', 'destinations', 'tags']:
            if field in route and route[field]:
                route[field] = json.dumps(route[field])

        # Convert headers dict to JSON string
        if 'headers' in route and route['headers']:
            route['headers'] = json.dumps(route['headers'])

    return routes_data


def load_routes(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    control_plane_id: str,
    update_tag: int,
) -> None:
    """
    Load routes into Neo4j using the KonnectRouteSchema.
    Load each route individually to handle different service IDs.
    """
    for route in data:
        service_id = route.get('service_id')
        load(
            neo4j_session,
            KonnectRouteSchema(),
            [route],
            lastupdated=update_tag,
            CONTROL_PLANE_ID=control_plane_id,
            SERVICE_ID=service_id,
        )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Remove stale routes from the graph.
    """
    query = """
    MATCH (r:KonnectRoute)
    WHERE r.lastupdated <> $UPDATE_TAG
    DETACH DELETE r
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
    Sync Kong Konnect Routes for all control planes.
    """
    control_plane_ids = get_control_plane_ids(neo4j_session)

    for cp_id in control_plane_ids:
        routes_data = get(api_token, api_url, cp_id)
        transformed_data = transform(routes_data, cp_id)
        load_routes(neo4j_session, transformed_data, cp_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
