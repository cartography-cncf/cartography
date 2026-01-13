import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.vertex.models import get_vertex_ai_locations
from cartography.models.gcp.vertex.dataset import GCPVertexAIDatasetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_vertex_ai_datasets_for_location(
    aiplatform: Resource,
    project_id: str,
    location: str,
) -> List[Dict]:
    """
    Gets all Vertex AI datasets for a specific location.
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
    url = f"{regional_endpoint}/v1/{parent}/datasets"

    # Use helper function to handle pagination and error handling
    return paginate_vertex_api(
        url=url,
        headers=headers,
        resource_type="datasets",
        response_key="datasets",
        location=location,
        project_id=project_id,
    )


@timeit
def transform_vertex_ai_datasets(datasets: List[Dict]) -> List[Dict]:
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
    datasets: List[Dict],
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
    common_job_parameters: Dict,
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
    common_job_parameters: Dict,
) -> None:
    """
    Get Vertex AI datasets, ingest to Neo4j, and clean up old data.
    """
    logger.info("Syncing Vertex AI datasets for project %s.", project_id)

    # Get all available locations for Vertex AI
    locations = get_vertex_ai_locations(aiplatform, project_id)

    # Collect datasets from all locations
    all_datasets = []
    for location in locations:
        datasets = get_vertex_ai_datasets_for_location(aiplatform, project_id, location)
        all_datasets.extend(datasets)

    # Transform and load datasets
    transformed_datasets = transform_vertex_ai_datasets(all_datasets)
    load_vertex_ai_datasets(
        neo4j_session, transformed_datasets, project_id, gcp_update_tag
    )

    # Clean up stale data
    cleanup_vertex_ai_datasets(neo4j_session, common_job_parameters)
