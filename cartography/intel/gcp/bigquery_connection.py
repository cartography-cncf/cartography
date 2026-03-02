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


def _get_locations(bigquery_client: Resource, project_id: str) -> list[str]:
    """
    List available BigQuery locations for a project using the BigQuery v2 API.

    The BigQuery Connection API does not expose a locations.list endpoint, so we
    use the BigQuery v2 API (datasets.list with a dry-run or projects API) instead.
    BigQuery v2 does not have a dedicated locations endpoint either, so we query
    the Cloud Resource Manager locations via the datasets API — specifically, we
    list datasets to discover which locations the project uses, and supplement with
    standard multi-region locations to ensure we don't miss connections in locations
    without datasets.

    Returns a deduplicated list of location IDs (e.g., ["us", "eu", "us-central1"]).
    """
    # Standard BigQuery multi-region and common regional locations.
    # Connections can exist in any of these even without datasets.
    # See https://cloud.google.com/bigquery/docs/locations
    default_locations = {"us", "eu"}

    # Discover additional locations from existing datasets
    locations: set[str] = set(default_locations)
    try:
        request = bigquery_client.datasets().list(projectId=project_id, all=True)
        while request is not None:
            response = gcp_api_execute_with_retry(request)
            for ds in response.get("datasets", []):
                loc = ds.get("location")
                if loc:
                    locations.add(loc.lower())
            request = bigquery_client.datasets().list_next(
                previous_request=request,
                previous_response=response,
            )
    except HttpError as e:
        logger.debug(
            "Could not list datasets to discover locations for project %s - %s. "
            "Using default locations only.",
            project_id,
            e,
        )

    return list(locations)


@timeit
def get_bigquery_connections(
    conn_client: Resource,
    project_id: str,
    bigquery_client: Resource | None = None,
) -> list[dict] | None:
    """
    Gets BigQuery connections for a project across all locations.

    The BigQuery Connection API does not support a wildcard location, so we
    discover locations from the BigQuery v2 API (via dataset locations) plus
    standard multi-region locations, then query each one individually.

    Args:
        conn_client: The bigqueryconnection v1 API client.
        project_id: The GCP project ID.
        bigquery_client: Optional BigQuery v2 API client for location discovery.
            If not provided, only default locations (us, eu) are queried.

    Returns:
        list[dict]: List of BigQuery connections
        None: If the API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    if bigquery_client is not None:
        locations = _get_locations(bigquery_client, project_id)
    else:
        locations = ["us", "eu"]

    connections: list[dict] = []
    for location in locations:
        parent = f"projects/{project_id}/locations/{location}"
        try:
            request = (
                conn_client.projects()
                .locations()
                .connections()
                .list(
                    parent=parent,
                )
            )
            while request is not None:
                response = gcp_api_execute_with_retry(request)
                connections.extend(response.get("connections", []))
                request = (
                    conn_client.projects()
                    .locations()
                    .connections()
                    .list_next(
                        previous_request=request,
                        previous_response=response,
                    )
                )
        except HttpError as e:
            if is_api_disabled_error(e) or e.resp.status in (403, 404):
                logger.warning(
                    "Could not retrieve BigQuery connections for %s/%s - %s. "
                    "Skipping location.",
                    project_id,
                    location,
                    e,
                )
                continue
            raise

    return connections


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
    bigquery_client: Resource | None = None,
) -> None:
    logger.info("Syncing BigQuery connections for project %s.", project_id)
    connections_raw = get_bigquery_connections(client, project_id, bigquery_client)

    if connections_raw is not None:
        connections = transform_connections(connections_raw, project_id)
        load_bigquery_connections(neo4j_session, connections, project_id, update_tag)

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["PROJECT_ID"] = project_id
        cleanup_bigquery_connections(neo4j_session, cleanup_job_params)
