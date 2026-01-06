import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.vertex.models import get_vertex_ai_locations
from cartography.models.gcp.vertex.training_pipeline import (
    GCPVertexAITrainingPipelineSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_vertex_ai_training_pipelines_for_location(
    aiplatform: Resource,
    project_id: str,
    location: str,
) -> List[Dict]:

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
    url = f"{regional_endpoint}/v1/{parent}/trainingPipelines"

    # Use helper function to handle pagination and error handling
    return paginate_vertex_api(
        url=url,
        headers=headers,
        resource_type="training pipelines",
        response_key="trainingPipelines",
        location=location,
        project_id=project_id,
    )


@timeit
def transform_training_pipelines(training_pipelines: List[Dict]) -> List[Dict]:

    transformed_pipelines = []

    for pipeline in training_pipelines:
        # Extract dataset ID from input data config (if Vertex AI Dataset is used)
        input_data_config = pipeline.get("inputDataConfig", {})
        # NOTE: datasetId is a numeric string, need to convert to full resource name
        dataset_id_numeric = input_data_config.get("datasetId")
        if dataset_id_numeric:
            # Extract project and location from pipeline name to build full dataset resource name
            # Pipeline name format: projects/{project}/locations/{location}/trainingPipelines/{id}
            pipeline_name = pipeline.get("name", "")
            parts = pipeline_name.split("/")
            if len(parts) >= 4:
                project = parts[1]
                location = parts[3]
                dataset_id = f"projects/{project}/locations/{location}/datasets/{dataset_id_numeric}"
            else:
                dataset_id = None
        else:
            dataset_id = None

        # Extract model ID (the model produced by this training pipeline)
        # NOTE: modelId is a short ID, need to convert to full resource name
        model_id_short = pipeline.get("modelId")
        if model_id_short:
            # Expand short ID to full resource name
            # Pipeline name format: projects/{project}/locations/{location}/trainingPipelines/{id}
            pipeline_name = pipeline.get("name", "")
            parts = pipeline_name.split("/")
            if len(parts) >= 4:
                project = parts[1]
                location = parts[3]
                model_id = (
                    f"projects/{project}/locations/{location}/models/{model_id_short}"
                )
            else:
                model_id = None
        else:
            # Fallback: check modelToUpload.name (already a full resource name)
            model_to_upload = pipeline.get("modelToUpload", {})
            model_id = model_to_upload.get("name")

        # Serialize nested dicts to JSON strings (Neo4j doesn't support nested dicts)
        error = pipeline.get("error")
        error_json = json.dumps(error) if error else None

        model_to_upload = pipeline.get("modelToUpload")
        model_to_upload_json = json.dumps(model_to_upload) if model_to_upload else None

        transformed_pipeline = {
            "id": pipeline.get("name"),  # Full resource name
            "name": pipeline.get("name"),
            "display_name": pipeline.get("displayName"),
            "create_time": pipeline.get("createTime"),
            "update_time": pipeline.get("updateTime"),
            "start_time": pipeline.get("startTime"),
            "end_time": pipeline.get("endTime"),
            "state": pipeline.get("state"),
            "error": error_json,
            "model_to_upload": model_to_upload_json,
            "training_task_definition": pipeline.get("trainingTaskDefinition"),
            # Relationship fields
            "dataset_id": dataset_id,  # For READS_FROM GCPVertexAIDataset relationship
            "model_id": model_id,  # For PRODUCES GCPVertexAIModel relationship
        }

        transformed_pipelines.append(transformed_pipeline)

    logger.info(
        f"Transformed {len(transformed_pipelines)} Vertex AI training pipelines"
    )
    return transformed_pipelines


@timeit
def load_training_pipelines(
    neo4j_session: neo4j.Session,
    training_pipelines: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:

    load(
        neo4j_session,
        GCPVertexAITrainingPipelineSchema(),
        training_pipelines,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_training_pipelines(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:

    GraphJob.from_node_schema(
        GCPVertexAITrainingPipelineSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


@timeit
def sync_training_pipelines(
    neo4j_session: neo4j.Session,
    aiplatform: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:

    logger.info("Syncing Vertex AI training pipelines for project %s.", project_id)

    # Get all available locations for Vertex AI
    locations = get_vertex_ai_locations(aiplatform, project_id)

    # Collect training pipelines from all locations
    all_training_pipelines = []
    for location in locations:
        training_pipelines = get_vertex_ai_training_pipelines_for_location(
            aiplatform, project_id, location
        )
        all_training_pipelines.extend(training_pipelines)

    # Transform and load training pipelines
    transformed_pipelines = transform_training_pipelines(all_training_pipelines)
    load_training_pipelines(
        neo4j_session, transformed_pipelines, project_id, gcp_update_tag
    )

    # Clean up stale data
    cleanup_training_pipelines(neo4j_session, common_job_parameters)
