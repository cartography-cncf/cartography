import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.vertex.models import get_vertex_ai_locations
from cartography.models.gcp.vertex.endpoint import GCPVertexAIEndpointSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_vertex_ai_endpoints_for_location(
    aiplatform: Resource,
    project_id: str,
    location: str,
) -> List[Dict]:
    """
    Gets all Vertex AI endpoints for a specific location.
    """
    from google.auth.transport.requests import Request as AuthRequest

    from cartography.intel.gcp.vertex.utils import paginate_vertex_api

    # Get credentials and refresh token if needed
    creds = aiplatform._http.credentials
    if not creds.valid:
        creds.refresh(AuthRequest())

    # Prepare request parameters
    regional_endpoint = f"https://{location}-aiplatform.googleapis.com"
    parent = f"projects/{project_id}/locations/{location}"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }
    url = f"{regional_endpoint}/v1/{parent}/endpoints"

    # Use helper function to handle pagination and error handling
    return paginate_vertex_api(
        url=url,
        headers=headers,
        resource_type="endpoints",
        response_key="endpoints",
        location=location,
        project_id=project_id,
    )


@timeit
def transform_vertex_ai_endpoints(endpoints: List[Dict]) -> List[Dict]:
    transformed_endpoints = []

    for endpoint in endpoints:
        transformed_endpoint = {
            "id": endpoint.get("name"),  # Full resource name
            "name": endpoint.get("name"),
            "display_name": endpoint.get("displayName"),
            "description": endpoint.get("description"),
            "create_time": endpoint.get("createTime"),
            "update_time": endpoint.get("updateTime"),
            "etag": endpoint.get("etag"),
            "labels": endpoint.get("labels"),
            "network": endpoint.get("network"),
        }

        transformed_endpoints.append(transformed_endpoint)

    logger.info(f"Transformed {len(transformed_endpoints)} Vertex AI endpoints")
    return transformed_endpoints


@timeit
def load_vertex_ai_endpoints(
    neo4j_session: neo4j.Session,
    endpoints: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Ingest GCP Vertex AI Endpoints to Neo4j.
    """
    load(
        neo4j_session,
        GCPVertexAIEndpointSchema(),
        endpoints,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_vertex_ai_endpoints(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Delete out-of-date GCP Vertex AI Endpoint nodes and relationships.
    """
    GraphJob.from_node_schema(GCPVertexAIEndpointSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_vertex_ai_endpoints(
    neo4j_session: neo4j.Session,
    aiplatform: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> List[Dict]:
    """
    Get Vertex AI endpoints, ingest to Neo4j, and clean up old data.
    """
    logger.info("Syncing Vertex AI endpoints for project %s.", project_id)

    # Get all available locations for Vertex AI
    locations = get_vertex_ai_locations(aiplatform, project_id)

    # Collect endpoints from all locations
    all_endpoints = []
    for location in locations:
        endpoints = get_vertex_ai_endpoints_for_location(
            aiplatform, project_id, location
        )
        all_endpoints.extend(endpoints)

    # Transform and load endpoints
    transformed_endpoints = transform_vertex_ai_endpoints(all_endpoints)
    load_vertex_ai_endpoints(
        neo4j_session, transformed_endpoints, project_id, gcp_update_tag
    )

    # Clean up stale data
    cleanup_vertex_ai_endpoints(neo4j_session, common_job_parameters)

    # Return raw endpoint data for deployed models sync
    return all_endpoints
