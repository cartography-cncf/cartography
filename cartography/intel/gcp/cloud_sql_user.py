import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudsql.user import GCPSqlUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_sql_users(client: Resource, project_id: str, instance_name: str) -> list[dict]:
    """
    Gets SQL Users for a given Instance.
    """
    users: list[dict] = []
    request = client.users().list(project=project_id, instance=instance_name)
    response = request.execute()
    users.extend(response.get("items", []))
    return users


def transform_sql_users(users_data: list[dict], instance_id: str) -> list[dict]:
    """
    Transforms the list of SQL User dicts for ingestion.
    """
    transformed: list[dict] = []
    for user in users_data:
        user_name = user.get("name")
        host = user.get("host")
        if not user_name:
            continue
        transformed.append(
            {
                "id": f"{instance_id}/users/{user_name}@{host}",
                "name": user_name,
                "host": host,
                "instance_id": instance_id,
            },
        )
    return transformed


@timeit
def load_sql_users(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPSqlUser nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPSqlUserSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_sql_users(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale Cloud SQL users.
    """
    GraphJob.from_node_schema(GCPSqlUserSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_sql_users(
    neo4j_session: neo4j.Session,
    client: Resource,
    instances: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Cloud SQL Users for project {project_id}.")
    all_users: list[dict] = []

    for inst in instances:
        instance_name = inst.get("name")
        instance_id = inst.get("selfLink")
        if not instance_name or not instance_id:
            continue

        try:
            users_raw = get_sql_users(client, project_id, instance_name)
            all_users.extend(transform_sql_users(users_raw, instance_id))
        except Exception:
            logger.warning(
                f"Failed to get SQL users for instance {instance_name}", exc_info=True
            )
            continue

    load_sql_users(neo4j_session, all_users, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_sql_users(neo4j_session, cleanup_job_params)
