import logging

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.models.gcp.bigquery.connection import GCPBigQueryConnectionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# BigQuery Connection API regions to query.
# The API requires a location; "-" means all locations.
_ALL_LOCATIONS = "-"


@timeit
def get_bigquery_connections(
    client: Resource,
    project_id: str,
) -> list[dict] | None:
    """
    Gets BigQuery connections for a project across all locations.

    Returns:
        list[dict]: List of BigQuery connections
        None: If the API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    try:
        connections: list[dict] = []
        parent = f"projects/{project_id}/locations/{_ALL_LOCATIONS}"
        request = client.projects().locations().connections().list(parent=parent)
        while request is not None:
            response = gcp_api_execute_with_retry(request)
            connections.extend(response.get("connections", []))
            request = (
                client.projects()
                .locations()
                .connections()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return connections
    except HttpError as e:
        if is_api_disabled_error(e):
            logger.warning(
                "Could not retrieve BigQuery connections on project %s due to permissions "
                "issues or API not enabled. Skipping sync to preserve existing data.",
                project_id,
            )
            return None
        raise


def transform_connections(connections_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for conn in connections_data:
        # Determine connection type from the oneOf fields in the API response
        connection_type = None
        for type_key in (
            "cloudSql",
            "aws",
            "azure",
            "cloudSpanner",
            "cloudResource",
            "spark",
        ):
            if type_key in conn:
                connection_type = type_key
                break

        cloud_sql = conn.get("cloudSql", {}) or {}
        aws = conn.get("aws", {}) or {}
        azure = conn.get("azure", {}) or {}
        cloud_resource = conn.get("cloudResource", {}) or {}
        transformed.append(
            {
                "name": conn["name"],
                "friendlyName": conn.get("friendlyName"),
                "description": conn.get("description"),
                "connection_type": connection_type,
                "creationTime": conn.get("creationTime"),
                "lastModifiedTime": conn.get("lastModifiedTime"),
                "hasCredential": conn.get("hasCredential"),
                "cloud_sql_instance_id": cloud_sql.get("instanceId"),
                "aws_role_arn": aws.get("accessRole", {}).get("iamRoleId"),
                "azure_app_client_id": azure.get("federatedApplicationClientId"),
                "service_account_id": cloud_resource.get("serviceAccountId"),
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_bigquery_connections(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPBigQueryConnectionSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_bigquery_connections(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(
        GCPBigQueryConnectionSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_bigquery_connections(
    neo4j_session: neo4j.Session,
    client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing BigQuery connections for project %s.", project_id)
    connections_raw = get_bigquery_connections(client, project_id)

    if connections_raw is not None:
        connections = transform_connections(connections_raw, project_id)
        load_bigquery_connections(neo4j_session, connections, project_id, update_tag)

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["PROJECT_ID"] = project_id
        cleanup_bigquery_connections(neo4j_session, cleanup_job_params)
