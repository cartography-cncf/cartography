import logging
from typing import Dict
from typing import List
from typing import Optional
from urllib.parse import urlparse

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.vertex.model import GCPVertexAIModelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_vertex_ai_locations(aiplatform: Resource, project_id: str) -> List[str]:
    """
    Gets all available Vertex AI locations for a project.
    Filters to only regions that commonly support Vertex AI to improve sync performance.
    """
    try:
        req = aiplatform.projects().locations().list(name=f"projects/{project_id}")
        res = req.execute()

        # Filter to only regions that commonly support Vertex AI
        # Reference: https://cloud.google.com/vertex-ai/docs/general/locations
        supported_regions = {
            "us-central1",
            "us-east1",
            "us-east4",
            "us-west1",
            "us-west2",
            "us-west3",
            "us-west4",
            "europe-west1",
            "europe-west2",
            "europe-west3",
            "europe-west4",
            "asia-east1",
            "asia-northeast1",
            "asia-northeast3",
            "asia-southeast1",
            "australia-southeast1",
            "northamerica-northeast1",
            "southamerica-east1",
        }

        locations = []
        all_locations = res.get("locations", [])
        for location in all_locations:
            # Extract location ID from the full path
            # Format: "projects/PROJECT_ID/locations/LOCATION_ID"
            location_id = location["locationId"]
            if location_id in supported_regions:
                locations.append(location_id)

        logger.info(
            f"Found {len(locations)} supported Vertex AI locations "
            f"(filtered from {len(all_locations)} total) for project {project_id}"
        )
        return locations

    except HttpError as e:
        error_reason = e.resp.get("reason", "unknown")
        if e.resp.status == 403:
            logger.warning(
                f"Access forbidden when trying to get Vertex AI locations for project {project_id}. "
                "Ensure the Vertex AI API is enabled and you have the necessary permissions.",
            )
        elif e.resp.status == 404:
            logger.warning(
                f"Vertex AI locations not found for project {project_id}. "
                "The Vertex AI API may not be enabled.",
            )
        else:
            logger.error(
                f"Error getting Vertex AI locations for project {project_id}: {error_reason}",
                exc_info=True,
            )
        return []


@timeit
def get_vertex_ai_models_for_location(
    aiplatform: Resource,
    project_id: str,
    location: str,
) -> List[Dict]:
    """
    Gets all Vertex AI models for a specific location.
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
    url = f"{regional_endpoint}/v1/{parent}/models"

    # Use helper function to handle pagination and error handling
    return paginate_vertex_api(
        url=url,
        headers=headers,
        resource_type="models",
        response_key="models",
        location=location,
        project_id=project_id,
    )


def _extract_bucket_name_from_gcs_uri(gcs_uri: Optional[str]) -> Optional[str]:
    """
    Extracts the bucket name from a GCS URI.

    :param gcs_uri: GCS URI in format 'gs://bucket-name/path/to/object'
    :return: The bucket name, or None if URI is invalid or not provided
    """
    if not gcs_uri:
        return None

    try:
        parsed = urlparse(gcs_uri)
        if parsed.scheme == "gs":
            return parsed.netloc
        return None
    except Exception as e:
        logger.warning(f"Failed to parse GCS URI '{gcs_uri}': {e}")
        return None


@timeit
def transform_vertex_ai_models(models: List[Dict]) -> List[Dict]:
    transformed_models = []

    for model in models:
        # Extract GCS bucket name from artifact URI for the STORED_IN relationship
        artifact_uri = model.get("artifactUri")
        gcs_bucket_id = _extract_bucket_name_from_gcs_uri(artifact_uri)

        transformed_model = {
            "id": model.get("name"),  # Full resource name
            "name": model.get("name"),
            "display_name": model.get("displayName"),
            "description": model.get("description"),
            "version_id": model.get("versionId"),
            "version_create_time": model.get("versionCreateTime"),
            "version_update_time": model.get("versionUpdateTime"),
            "create_time": model.get("createTime"),
            "update_time": model.get("updateTime"),
            "artifact_uri": artifact_uri,
            "etag": model.get("etag"),
            "labels": model.get("labels"),
            "training_pipeline": model.get("trainingPipeline"),
            "gcs_bucket_id": gcs_bucket_id,  # For STORED_IN relationship
        }

        transformed_models.append(transformed_model)

    logger.info(f"Transformed {len(transformed_models)} Vertex AI models")
    return transformed_models


@timeit
def load_vertex_ai_models(
    neo4j_session: neo4j.Session,
    models: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:

    load(
        neo4j_session,
        GCPVertexAIModelSchema(),
        models,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_vertex_ai_models(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:

    GraphJob.from_node_schema(GCPVertexAIModelSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_vertex_ai_models(
    neo4j_session: neo4j.Session,
    aiplatform: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:

    logger.info("Syncing Vertex AI models for project %s.", project_id)

    # Get all available locations for Vertex AI
    locations = get_vertex_ai_locations(aiplatform, project_id)

    # Collect models from all locations
    all_models = []
    for location in locations:
        models = get_vertex_ai_models_for_location(aiplatform, project_id, location)
        all_models.extend(models)

    # Transform and load models
    transformed_models = transform_vertex_ai_models(all_models)
    load_vertex_ai_models(neo4j_session, transformed_models, project_id, gcp_update_tag)

    # Clean up stale data
    cleanup_vertex_ai_models(neo4j_session, common_job_parameters)
