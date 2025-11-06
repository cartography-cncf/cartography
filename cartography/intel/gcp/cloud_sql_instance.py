import logging

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudsql.instance import GCPSqlInstanceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_sql_instances(client: Resource, project_id: str) -> list[dict]:
    """
    Gets GCP SQL Instances for a project.
    """
    instances: list[dict] = []
    try:
        request = client.instances().list(project=project_id)
        while request is not None:
            response = request.execute()
            instances.extend(response.get("items", []))
            request = client.instances().list_next(
                previous_request=request,
                previous_response=response,
            )
        return instances
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get SQL instances for project {project_id} due to permissions or auth error: {e}",
        )
        raise


def transform_sql_instances(instances_data: list[dict], project_id: str) -> list[dict]:
    """
    Transforms the list of SQL Instance dicts for ingestion.
    """
    transformed: list[dict] = []
    for inst in instances_data:
        transformed.append(
            {
                "selfLink": inst.get("selfLink"),
                "name": inst.get("name"),
                "databaseVersion": inst.get("databaseVersion"),
                "region": inst.get("region"),
                "gceZone": inst.get("gceZone"),
                "state": inst.get("state"),
                "backendType": inst.get("backendType"),
                "network_id": inst.get("settings", {})
                .get("ipConfiguration", {})
                .get("privateNetwork"),
                "service_account_email": inst.get("serviceAccountEmailAddress"),
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
) -> list[dict]:
    """
    Syncs GCP SQL Instances and returns the raw instance data.
    """
    logger.info(f"Syncing Cloud SQL Instances for project {project_id}.")
    instances_raw = get_sql_instances(client, project_id)
    if not instances_raw:
        logger.info(f"No Cloud SQL instances found for project {project_id}.")

    instances = transform_sql_instances(instances_raw, project_id)
    load_sql_instances(neo4j_session, instances, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_sql_instances(neo4j_session, cleanup_job_params)

    return instances_raw
