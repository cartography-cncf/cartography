import logging
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.vertex.deployed_model import GCPVertexAIDeployedModelSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def transform_deployed_models_from_endpoints(endpoints: List[Dict]) -> List[Dict]:
    """
    Extracts and transforms deployed models from endpoint API responses.

    Deployed models are nested within endpoint responses rather than having
    their own API endpoint. This function extracts them and transforms them
    to the Neo4j schema format.
    """
    transformed_deployed_models = []

    for endpoint in endpoints:
        endpoint_name = endpoint.get("name")

        # Each endpoint contains a deployedModels array
        for deployed_model in endpoint.get("deployedModels", []):
            # Create a composite ID from endpoint and deployed model ID
            deployed_model_id = deployed_model.get("id")
            composite_id = f"{endpoint_name}/deployedModels/{deployed_model_id}"

            # Transform to schema format
            transformed = {
                "id": composite_id,  # Unique composite ID
                "deployed_model_id": deployed_model_id,
                "model": deployed_model.get(
                    "model"
                ),  # Model resource name for INSTANCE_OF relationship
                "display_name": deployed_model.get("displayName"),
                "create_time": deployed_model.get("createTime"),
                "service_account": deployed_model.get("serviceAccount"),
                "enable_access_logging": deployed_model.get("enableAccessLogging"),
                "endpoint_id": endpoint_name,  # For SERVES relationship
            }

            transformed_deployed_models.append(transformed)

    logger.info(
        f"Transformed {len(transformed_deployed_models)} deployed models from {len(endpoints)} endpoints"
    )
    return transformed_deployed_models


@timeit
def load_vertex_ai_deployed_models(
    neo4j_session: neo4j.Session,
    deployed_models: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:

    load(
        neo4j_session,
        GCPVertexAIDeployedModelSchema(),
        deployed_models,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_vertex_ai_deployed_models(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:

    GraphJob.from_node_schema(
        GCPVertexAIDeployedModelSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


@timeit
def sync_vertex_ai_deployed_models(
    neo4j_session: neo4j.Session,
    endpoints: List[Dict],
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:

    logger.info("Syncing Vertex AI deployed models for project %s.", project_id)

    # Extract and transform deployed models from endpoint data
    transformed_deployed_models = transform_deployed_models_from_endpoints(endpoints)

    # Load deployed models to Neo4j
    load_vertex_ai_deployed_models(
        neo4j_session, transformed_deployed_models, project_id, gcp_update_tag
    )

    # Clean up stale data
    cleanup_vertex_ai_deployed_models(neo4j_session, common_job_parameters)
