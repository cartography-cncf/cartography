import json
import logging

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.clients import build_vertex_ai_endpoint_client
from cartography.intel.gcp.vertex.models import get_vertex_ai_locations
from cartography.intel.gcp.vertex.utils import fetch_vertex_ai_resources_for_locations
from cartography.intel.gcp.vertex.utils import get_vertex_credentials
from cartography.intel.gcp.vertex.utils import list_vertex_ai_resources_for_location
from cartography.models.gcp.vertex.endpoint import GCPVertexAIEndpointSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_vertex_ai_endpoints_for_location(
    credentials: GoogleCredentials,
    project_id: str,
    location: str,
) -> list[dict]:
    """
    Gets all Vertex AI endpoints for a specific location.
    """
    parent = f"projects/{project_id}/locations/{location}"
    return list_vertex_ai_resources_for_location(
        fetcher=lambda: build_vertex_ai_endpoint_client(
            location,
            credentials=credentials,
        ).list_endpoints(parent=parent),
        resource_type="endpoints",
        location=location,
        project_id=project_id,
    )


@timeit
def transform_vertex_ai_endpoints(endpoints: list[dict]) -> list[dict]:
    transformed_endpoints = []

    for endpoint in endpoints:
        # Neo4j properties cannot store maps; serialize map-like fields to JSON.
        labels = endpoint.get("labels")
        labels_json = json.dumps(labels) if labels else None

        transformed_endpoint = {
            "id": endpoint.get("name"),  # Full resource name
            "name": endpoint.get("name"),
            "display_name": endpoint.get("displayName"),
            "description": endpoint.get("description"),
            "create_time": endpoint.get("createTime"),
            "update_time": endpoint.get("updateTime"),
            "etag": endpoint.get("etag"),
            "labels": labels_json,
            "network": endpoint.get("network"),
        }

        transformed_endpoints.append(transformed_endpoint)

    logger.info(f"Transformed {len(transformed_endpoints)} Vertex AI endpoints")
    return transformed_endpoints


@timeit
def load_vertex_ai_endpoints(
    neo4j_session: neo4j.Session,
    endpoints: list[dict],
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
    common_job_parameters: dict,
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
    common_job_parameters: dict,
    locations: list[str] | None = None,
) -> list[dict]:
    """
    Get Vertex AI endpoints, ingest to Neo4j, and clean up old data.
    """
    logger.info("Syncing Vertex AI endpoints for project %s.", project_id)

    if locations is None:
        locations = get_vertex_ai_locations(aiplatform, project_id)
        if locations is None:
            logger.warning(
                "Skipping Vertex AI endpoints sync for project %s to preserve existing data "
                "because Vertex AI location discovery failed.",
                project_id,
            )
            return []
    else:
        logger.debug(
            "Using %s cached Vertex AI locations for endpoints in project %s.",
            len(locations),
            project_id,
        )

    credentials = get_vertex_credentials(aiplatform)
    all_endpoints = fetch_vertex_ai_resources_for_locations(
        locations=locations,
        project_id=project_id,
        resource_type="endpoints",
        fetch_for_location=lambda location: get_vertex_ai_endpoints_for_location(
            credentials,
            project_id,
            location,
        ),
    )

    # Transform and load endpoints
    transformed_endpoints = transform_vertex_ai_endpoints(all_endpoints)
    load_vertex_ai_endpoints(
        neo4j_session, transformed_endpoints, project_id, gcp_update_tag
    )

    # Clean up stale data
    cleanup_vertex_ai_endpoints(neo4j_session, common_job_parameters)

    # Return raw endpoint data for deployed models sync
    return all_endpoints
