import json
import logging

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.clients import build_vertex_ai_dataset_client
from cartography.intel.gcp.vertex.models import get_vertex_ai_locations
from cartography.intel.gcp.vertex.utils import fetch_vertex_ai_resources_for_locations
from cartography.intel.gcp.vertex.utils import get_vertex_credentials
from cartography.intel.gcp.vertex.utils import list_vertex_ai_resources_for_location
from cartography.models.gcp.vertex.dataset import GCPVertexAIDatasetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_vertex_ai_datasets_for_location(
    credentials: GoogleCredentials,
    project_id: str,
    location: str,
) -> list[dict]:
    """
    Gets all Vertex AI datasets for a specific location.
    """
    parent = f"projects/{project_id}/locations/{location}"
    return list_vertex_ai_resources_for_location(
        fetcher=lambda: build_vertex_ai_dataset_client(
            location,
            credentials=credentials,
        ).list_datasets(parent=parent),
        resource_type="datasets",
        location=location,
        project_id=project_id,
    )


@timeit
def transform_vertex_ai_datasets(datasets: list[dict]) -> list[dict]:
    """
    Transform Vertex AI dataset API responses into format expected by the schema.
    """
    transformed_datasets = []

    for dataset in datasets:
        # Serialize metadata to JSON string if present (Neo4j doesn't support nested dicts)
        metadata = dataset.get("metadata")
        metadata_json = json.dumps(metadata) if metadata else None

        # Serialize encryption_spec to JSON string if present
        encryption_spec = dataset.get("encryptionSpec")
        encryption_spec_json = json.dumps(encryption_spec) if encryption_spec else None

        # Serialize labels to JSON string if present
        labels = dataset.get("labels")
        labels_json = json.dumps(labels) if labels else None

        transformed_dataset = {
            "id": dataset.get("name"),  # Full resource name
            "name": dataset.get("name"),
            "display_name": dataset.get("displayName"),
            "description": dataset.get("description"),
            "labels": labels_json,
            "create_time": dataset.get("createTime"),
            "update_time": dataset.get("updateTime"),
            "etag": dataset.get("etag"),
            "data_item_count": dataset.get("dataItemCount"),
            "metadata_schema_uri": dataset.get("metadataSchemaUri"),
            "metadata": metadata_json,
            "encryption_spec": encryption_spec_json,
        }

        transformed_datasets.append(transformed_dataset)

    logger.info(f"Transformed {len(transformed_datasets)} Vertex AI datasets")
    return transformed_datasets


@timeit
def load_vertex_ai_datasets(
    neo4j_session: neo4j.Session,
    datasets: list[dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Ingest GCP Vertex AI Datasets to Neo4j.
    """
    load(
        neo4j_session,
        GCPVertexAIDatasetSchema(),
        datasets,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_vertex_ai_datasets(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP Vertex AI Dataset nodes and relationships.
    """
    GraphJob.from_node_schema(GCPVertexAIDatasetSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_vertex_ai_datasets(
    neo4j_session: neo4j.Session,
    aiplatform: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
    locations: list[str] | None = None,
) -> None:
    """
    Get Vertex AI datasets, ingest to Neo4j, and clean up old data.
    """
    logger.info("Syncing Vertex AI datasets for project %s.", project_id)

    if locations is None:
        locations = get_vertex_ai_locations(aiplatform, project_id)
        if locations is None:
            logger.warning(
                "Skipping Vertex AI datasets sync for project %s to preserve existing data "
                "because Vertex AI location discovery failed.",
                project_id,
            )
            return
    else:
        logger.debug(
            "Using %s cached Vertex AI locations for datasets in project %s.",
            len(locations),
            project_id,
        )

    credentials = get_vertex_credentials(aiplatform)
    all_datasets = fetch_vertex_ai_resources_for_locations(
        locations=locations,
        project_id=project_id,
        resource_type="datasets",
        fetch_for_location=lambda location: get_vertex_ai_datasets_for_location(
            credentials,
            project_id,
            location,
        ),
    )

    # Transform and load datasets
    transformed_datasets = transform_vertex_ai_datasets(all_datasets)
    load_vertex_ai_datasets(
        neo4j_session, transformed_datasets, project_id, gcp_update_tag
    )

    # Clean up stale data
    cleanup_vertex_ai_datasets(neo4j_session, common_job_parameters)
