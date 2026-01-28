import json
import logging

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.models.gcp.cloudsql.instance import GCPSqlInstanceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_sql_instances(client: Resource, project_id: str) -> list[dict] | None:
    """
    Gets GCP SQL Instances for a project.

    Returns:
        list[dict]: List of SQL instances (empty list if project has no instances)
        None: If the Cloud SQL Admin API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    instances: list[dict] = []
    try:
        request = client.instances().list(project=project_id)
        while request is not None:
            response = gcp_api_execute_with_retry(request)
            instances.extend(response.get("items", []))
            request = client.instances().list_next(
                previous_request=request,
                previous_response=response,
            )
        return instances
    except HttpError as e:
        if is_api_disabled_error(e):
            logger.warning(
                "Could not retrieve Cloud SQL instances on project %s due to permissions "
                "issues or API not enabled. Skipping sync to preserve existing data.",
                project_id,
            )
            return None
        raise


def transform_sql_instances(instances_data: list[dict], project_id: str) -> list[dict]:
    """
    Transforms the list of SQL Instance dicts for ingestion.
    """
    transformed: list[dict] = []
    for inst in instances_data:
        settings = inst.get("settings", {})
        ip_config = settings.get("ipConfiguration", {})
        backup_config = settings.get("backupConfiguration", {})

        # Serialize complex objects to JSON strings
        ip_addresses_json = None
        if inst.get("ipAddresses"):
            ip_addresses_json = json.dumps(inst.get("ipAddresses"))

        backup_config_json = None
        if backup_config:
            backup_config_json = json.dumps(backup_config)

        # Normalize privateNetwork to match GCPVpc ID format
        # Cloud SQL API returns: /projects/.../global/networks/...
        # GCPVpc uses: projects/.../global/networks/... (no leading slash)
        network_id = ip_config.get("privateNetwork")
        if network_id and network_id.startswith("/"):
            network_id = network_id.lstrip("/")

        transformed.append(
            {
                "selfLink": inst.get("selfLink"),
                "name": inst.get("name"),
                "databaseVersion": inst.get("databaseVersion"),
                "region": inst.get("region"),
                "gceZone": inst.get("gceZone"),
                "state": inst.get("state"),
                "backendType": inst.get("backendType"),
                "service_account_email": inst.get("serviceAccountEmailAddress"),
                "connectionName": inst.get("connectionName"),
                "tier": settings.get("tier"),
                "disk_size_gb": settings.get("dataDiskSizeGb"),
                "disk_type": settings.get("dataDiskType"),
                "availability_type": settings.get("availabilityType"),
                "backup_enabled": backup_config.get("enabled"),
                "require_ssl": ip_config.get("requireSsl"),
                "network_id": network_id,
                "ip_addresses": ip_addresses_json,
                "backup_configuration": backup_config_json,
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_sql_instances(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPSqlInstance nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPSqlInstanceSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_sql_instances(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale Cloud SQL instances.
    """
    GraphJob.from_node_schema(GCPSqlInstanceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_sql_instances(
    neo4j_session: neo4j.Session,
    client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict] | None:
    """
    Syncs GCP SQL Instances and returns the raw instance data.
    """
    logger.info(f"Syncing Cloud SQL Instances for project {project_id}.")
    instances_raw = get_sql_instances(client, project_id)

    # Only load and cleanup if we successfully retrieved data (even if empty list).
    # If get() returned None due to API not enabled, skip both to preserve existing data.
    if instances_raw is not None:
        if not instances_raw:
            logger.info(f"No Cloud SQL instances found for project {project_id}.")

        instances = transform_sql_instances(instances_raw, project_id)
        load_sql_instances(neo4j_session, instances, project_id, update_tag)

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["PROJECT_ID"] = project_id
        cleanup_sql_instances(neo4j_session, cleanup_job_params)

    return instances_raw
