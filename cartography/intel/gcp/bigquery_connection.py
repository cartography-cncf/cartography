import logging

import neo4j
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied
from google.cloud.bigquery import Client as BigQueryClient
from google.cloud.bigquery_connection_v1 import ConnectionServiceClient
from google.cloud.bigquery_connection_v1.types import Connection

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import proto_message_to_dict
from cartography.models.gcp.bigquery.connection import GCPBigQueryConnectionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _get_locations_from_datasets(datasets_raw: list[dict] | None) -> list[str]:
    default_locations = {"us", "eu"}
    locations = set(default_locations)

    for dataset in datasets_raw or []:
        loc = dataset.get("location")
        if loc:
            locations.add(loc.lower())

    return sorted(locations)


def _get_locations(
    bigquery_client: BigQueryClient,
    project_id: str,
    datasets_raw: list[dict] | None = None,
) -> list[str]:
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
    if datasets_raw is not None:
        return _get_locations_from_datasets(datasets_raw)

    # Discover additional locations from existing datasets.
    locations = set(_get_locations_from_datasets(None))
    try:
        dataset_items = list(
            bigquery_client.list_datasets(project=project_id, include_all=True)
        )
    except GoogleAPICallError as e:  # pragma: no cover - best-effort fallback
        logger.debug(
            "Could not list datasets to discover BigQuery connection locations for project %s - %s. "
            "Using default locations only.",
            project_id,
            e,
        )
        return sorted(locations)

    for dataset_item in dataset_items:
        try:
            dataset = bigquery_client.get_dataset(
                f"{dataset_item.project}.{dataset_item.dataset_id}"
            )
            loc = dataset.location
            if loc:
                locations.add(loc.lower())
        except GoogleAPICallError as e:  # pragma: no cover - best-effort fallback
            logger.debug(
                "Could not retrieve dataset detail to discover locations for %s.%s - %s. "
                "Continuing.",
                dataset_item.project,
                dataset_item.dataset_id,
                e,
            )

    return sorted(locations)


def _connection_to_dict(connection: Connection) -> dict:
    connection_type = connection._pb.WhichOneof("properties")
    cloud_sql = connection.cloud_sql
    aws = connection.aws
    azure = connection.azure
    cloud_resource = connection.cloud_resource
    connection_dict = proto_message_to_dict(connection)
    data = {
        "name": connection.name,
        "friendlyName": connection.friendly_name or None,
        "description": connection.description or None,
        "creationTime": (
            str(connection.creation_time)
            if connection.creation_time
            else connection_dict.get("creationTime")
        ),
        "lastModifiedTime": (
            str(connection.last_modified_time)
            if connection.last_modified_time
            else connection_dict.get("lastModifiedTime")
        ),
        "hasCredential": connection.has_credential,
    }
    if connection_type == "cloud_sql" and cloud_sql.instance_id:
        data["cloudSql"] = {"instanceId": cloud_sql.instance_id}
    elif connection_type == "aws" and aws.access_role.iam_role_id:
        data["aws"] = {"accessRole": {"iamRoleId": aws.access_role.iam_role_id}}
    elif connection_type == "azure" and azure.federated_application_client_id:
        data["azure"] = {
            "federatedApplicationClientId": azure.federated_application_client_id,
        }
    elif connection_type == "cloud_resource" and cloud_resource.service_account_id:
        data["cloudResource"] = {"serviceAccountId": cloud_resource.service_account_id}
    elif connection_type == "spark":
        data["spark"] = connection_dict.get("spark", {})
    elif connection_type == "cloud_spanner":
        data["cloudSpanner"] = connection_dict.get("cloudSpanner", {})

    return data


@timeit
def get_bigquery_connections(
    conn_client: ConnectionServiceClient,
    project_id: str,
    bigquery_client: BigQueryClient | None = None,
    datasets_raw: list[dict] | None = None,
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
    """
    if datasets_raw is not None:
        locations = _get_locations_from_datasets(datasets_raw)
    elif bigquery_client is not None:
        locations = _get_locations(bigquery_client, project_id)
    else:
        locations = ["us", "eu"]

    connections: list[dict] = []
    queried_any_location = False
    had_permission_denied = False
    for location in locations:
        parent = f"projects/{project_id}/locations/{location}"
        try:
            pager = conn_client.list_connections(parent=parent)
            queried_any_location = True
            connections.extend(_connection_to_dict(connection) for connection in pager)
        except PermissionDenied as e:
            had_permission_denied = True
            logger.warning(
                "Could not retrieve BigQuery connections for %s/%s - %s. "
                "Skipping location.",
                project_id,
                location,
                e,
            )
            continue

    if had_permission_denied and not queried_any_location:
        logger.warning(
            "Could not retrieve BigQuery connections on project %s due to permissions "
            "issues. Skipping sync to preserve existing data.",
            project_id,
        )
        return None

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
    client: ConnectionServiceClient,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    bigquery_client: BigQueryClient | None = None,
    datasets_raw: list[dict] | None = None,
) -> None:
    logger.info("Syncing BigQuery connections for project %s.", project_id)
    connections_raw = get_bigquery_connections(
        client,
        project_id,
        bigquery_client,
        datasets_raw,
    )

    if connections_raw is not None:
        connections = transform_connections(connections_raw, project_id)
        load_bigquery_connections(neo4j_session, connections, project_id, update_tag)

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["PROJECT_ID"] = project_id
        cleanup_bigquery_connections(neo4j_session, cleanup_job_params)
