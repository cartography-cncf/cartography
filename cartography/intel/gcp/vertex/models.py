import json
import logging
import re
from urllib.parse import urlparse

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.clients import build_vertex_ai_model_client
from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.intel.gcp.vertex.utils import fetch_vertex_ai_resources_for_locations
from cartography.intel.gcp.vertex.utils import get_vertex_credentials
from cartography.intel.gcp.vertex.utils import list_vertex_ai_resources_for_location
from cartography.models.gcp.vertex.model import GCPVertexAIModelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_VERTEX_AI_REGIONAL_LOCATION_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+[0-9]$")


def _is_vertex_ai_regional_location(location_id: str) -> bool:
    return bool(_VERTEX_AI_REGIONAL_LOCATION_RE.match(location_id))


@timeit
def get_vertex_ai_locations(
    aiplatform: Resource,
    project_id: str,
) -> list[str] | None:
    """
    Gets all available Vertex AI locations for a project.

    We trust the service's reported location list instead of maintaining a
    client-side allowlist, which can drift behind newly launched regions.
    """
    try:
        req = aiplatform.projects().locations().list(name=f"projects/{project_id}")
        res = req.execute()

        locations = set()
        skipped_locations = set()
        all_locations = res.get("locations", [])
        for location in all_locations:
            location_id = location.get("locationId")
            if not location_id:
                continue
            if _is_vertex_ai_regional_location(location_id):
                locations.add(location_id)
            else:
                skipped_locations.add(location_id)

        sorted_locations = sorted(locations)
        logger.info(
            "Found %s regional Vertex AI locations from the service for project %s.",
            len(sorted_locations),
            project_id,
        )
        if skipped_locations:
            logger.debug(
                "Skipping non-regional Vertex AI locations for project %s: %s",
                project_id,
                sorted(skipped_locations),
            )
        logger.debug(
            "Vertex AI locations for project %s: %s",
            project_id,
            sorted_locations,
        )
        return sorted_locations

    except HttpError as e:
        category = classify_gcp_http_error(e)
        if category in ("api_disabled", "forbidden"):
            logger.warning(
                "Access forbidden when trying to get Vertex AI locations for project %s. "
                "Ensure the Vertex AI API is enabled and you have the necessary permissions.",
                project_id,
            )
        elif category == "not_found":
            logger.warning(
                "Vertex AI locations not found for project %s. "
                "The Vertex AI API may not be enabled.",
                project_id,
            )
        else:
            logger.error(
                "Error getting Vertex AI locations for project %s: %s",
                project_id,
                summarize_gcp_http_error(e),
                exc_info=True,
            )
        return None


@timeit
def get_vertex_ai_models_for_location(
    credentials: GoogleCredentials,
    project_id: str,
    location: str,
) -> list[dict]:
    """
    Gets all Vertex AI models for a specific location.
    """
    parent = f"projects/{project_id}/locations/{location}"
    return list_vertex_ai_resources_for_location(
        fetcher=lambda: build_vertex_ai_model_client(
            location,
            credentials=credentials,
        ).list_models(parent=parent),
        resource_type="models",
        location=location,
        project_id=project_id,
    )


def _extract_bucket_name_from_gcs_uri(gcs_uri: str | None) -> str | None:
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
def transform_vertex_ai_models(models: list[dict]) -> list[dict]:
    transformed_models = []

    for model in models:
        # Extract GCS bucket name from artifact URI for the STORED_IN relationship
        artifact_uri = model.get("artifactUri")
        gcs_bucket_id = _extract_bucket_name_from_gcs_uri(artifact_uri)

        # Neo4j properties cannot store maps; serialize map-like fields to JSON.
        labels = model.get("labels")
        labels_json = json.dumps(labels) if labels else None

        training_pipeline = model.get("trainingPipeline")
        training_pipeline_value: str | None
        if isinstance(training_pipeline, (dict, list)):
            training_pipeline_value = json.dumps(training_pipeline)
        elif isinstance(training_pipeline, str):
            training_pipeline_value = training_pipeline
        elif training_pipeline is None:
            training_pipeline_value = None
        else:
            training_pipeline_value = str(training_pipeline)

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
            "labels": labels_json,
            "training_pipeline": training_pipeline_value,
            "gcs_bucket_id": gcs_bucket_id,  # For STORED_IN relationship
        }

        transformed_models.append(transformed_model)

    logger.info(f"Transformed {len(transformed_models)} Vertex AI models")
    return transformed_models


@timeit
def load_vertex_ai_models(
    neo4j_session: neo4j.Session,
    models: list[dict],
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
    common_job_parameters: dict,
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
    common_job_parameters: dict,
    locations: list[str] | None = None,
) -> None:

    logger.info("Syncing Vertex AI models for project %s.", project_id)

    if locations is None:
        locations = get_vertex_ai_locations(aiplatform, project_id)
        if locations is None:
            logger.warning(
                "Skipping Vertex AI models sync for project %s to preserve existing data "
                "because Vertex AI location discovery failed.",
                project_id,
            )
            return
    else:
        logger.debug(
            "Using %s cached Vertex AI locations for models in project %s.",
            len(locations),
            project_id,
        )

    credentials = get_vertex_credentials(aiplatform)
    all_models = fetch_vertex_ai_resources_for_locations(
        locations=locations,
        project_id=project_id,
        resource_type="models",
        fetch_for_location=lambda location: get_vertex_ai_models_for_location(
            credentials,
            project_id,
            location,
        ),
    )

    # Transform and load models
    transformed_models = transform_vertex_ai_models(all_models)
    load_vertex_ai_models(neo4j_session, transformed_models, project_id, gcp_update_tag)

    # Clean up stale data
    cleanup_vertex_ai_models(neo4j_session, common_job_parameters)
