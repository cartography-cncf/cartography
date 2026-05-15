import json
import logging

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.clients import build_vertex_ai_feature_registry_client
from cartography.intel.gcp.vertex.models import get_vertex_ai_locations
from cartography.intel.gcp.vertex.utils import fetch_vertex_ai_resources_for_locations
from cartography.intel.gcp.vertex.utils import get_vertex_credentials
from cartography.intel.gcp.vertex.utils import list_vertex_ai_resources_for_location
from cartography.models.gcp.vertex.feature_group import GCPVertexAIFeatureGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_feature_groups_for_location(
    credentials: GoogleCredentials,
    project_id: str,
    location: str,
) -> list[dict]:
    """
    Gets all Vertex AI Feature Groups for a specific location.

    Feature Groups are the new architecture for Vertex AI Feature Store, replacing the legacy
    FeatureStore → EntityType → Feature hierarchy.
    """
    parent = f"projects/{project_id}/locations/{location}"
    return list_vertex_ai_resources_for_location(
        fetcher=lambda: build_vertex_ai_feature_registry_client(
            location,
            credentials=credentials,
        ).list_feature_groups(parent=parent),
        resource_type="feature groups",
        location=location,
        project_id=project_id,
    )


@timeit
def transform_feature_groups(feature_groups: list[dict]) -> list[dict]:
    transformed_groups = []

    for group in feature_groups:
        # Extract BigQuery source information
        bigquery_config = group.get("bigQuery", {})
        bigquery_source = bigquery_config.get("bigQuerySource", {})
        bigquery_source_uri = bigquery_source.get("inputUri")

        # Extract entity ID columns (array of column names)
        entity_id_columns = bigquery_config.get("entityIdColumns", [])
        entity_id_columns_json = (
            json.dumps(entity_id_columns) if entity_id_columns else None
        )

        # Extract timestamp column (if using time series features)
        time_series = bigquery_config.get("timeSeries", {})
        timestamp_column = time_series.get("timestampColumn")

        # Serialize labels to JSON string if present
        labels = group.get("labels")
        labels_json = json.dumps(labels) if labels else None

        transformed_group = {
            "id": group.get("name"),  # Full resource name
            "name": group.get("name"),
            "description": group.get("description"),
            "labels": labels_json,
            "create_time": group.get("createTime"),
            "update_time": group.get("updateTime"),
            "etag": group.get("etag"),
            "bigquery_source_uri": bigquery_source_uri,
            "entity_id_columns": entity_id_columns_json,
            "timestamp_column": timestamp_column,
        }

        transformed_groups.append(transformed_group)

    logger.info(f"Transformed {len(transformed_groups)} Vertex AI Feature Groups")
    return transformed_groups


@timeit
def load_feature_groups(
    neo4j_session: neo4j.Session,
    feature_groups: list[dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:

    load(
        neo4j_session,
        GCPVertexAIFeatureGroupSchema(),
        feature_groups,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_feature_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:

    GraphJob.from_node_schema(
        GCPVertexAIFeatureGroupSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


@timeit
def sync_feature_groups(
    neo4j_session: neo4j.Session,
    aiplatform: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
    locations: list[str] | None = None,
) -> None:

    logger.info("Syncing Vertex AI Feature Groups for project %s.", project_id)

    if locations is None:
        locations = get_vertex_ai_locations(aiplatform, project_id)
        if locations is None:
            logger.warning(
                "Skipping Vertex AI Feature Groups sync for project %s to preserve existing "
                "data because Vertex AI location discovery failed.",
                project_id,
            )
            return
    else:
        logger.debug(
            "Using %s cached Vertex AI locations for feature groups in project %s.",
            len(locations),
            project_id,
        )

    credentials = get_vertex_credentials(aiplatform)
    all_feature_groups = fetch_vertex_ai_resources_for_locations(
        locations=locations,
        project_id=project_id,
        resource_type="feature groups",
        fetch_for_location=lambda location: get_feature_groups_for_location(
            credentials,
            project_id,
            location,
        ),
    )

    # Transform and load feature groups
    transformed_groups = transform_feature_groups(all_feature_groups)
    load_feature_groups(neo4j_session, transformed_groups, project_id, gcp_update_tag)

    # Clean up stale data
    cleanup_feature_groups(neo4j_session, common_job_parameters)
