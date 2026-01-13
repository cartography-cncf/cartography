import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudsql.database import GCPSqlDatabaseSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_sql_databases(
    client: Resource,
    project_id: str,
    instance_name: str,
) -> list[dict]:
    """
    Gets SQL Databases for a given Instance.
    """
    databases: list[dict] = []
    request = client.databases().list(project=project_id, instance=instance_name)
    response = request.execute()
    databases.extend(response.get("items", []))
    return databases


def transform_sql_databases(databases_data: list[dict], instance_id: str) -> list[dict]:
    """
    Transforms the list of SQL Database dicts for ingestion.
    """
    transformed: list[dict] = []
    for db in databases_data:
        db_name = db.get("name")
        if not db_name:
            continue
        transformed.append(
            {
                "id": f"{instance_id}/databases/{db_name}",
                "name": db_name,
                "charset": db.get("charset"),
                "collation": db.get("collation"),
                "instance_id": instance_id,
            },
        )
    return transformed


@timeit
def load_sql_databases(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPSqlDatabase nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPSqlDatabaseSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_sql_databases(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale Cloud SQL databases.
    """
    GraphJob.from_node_schema(GCPSqlDatabaseSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_sql_databases(
    neo4j_session: neo4j.Session,
    client: Resource,
    instances: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Cloud SQL Databases for project {project_id}.")
    all_databases: list[dict] = []

    for inst in instances:
        instance_name = inst.get("name")
        instance_id = inst.get("selfLink")
        if not instance_name or not instance_id:
            continue

        try:
            databases_raw = get_sql_databases(client, project_id, instance_name)
            all_databases.extend(transform_sql_databases(databases_raw, instance_id))
        except Exception:
            logger.warning(
                f"Failed to get SQL databases for instance {instance_name}",
                exc_info=True,
            )
            continue

    load_sql_databases(neo4j_session, all_databases, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_sql_databases(neo4j_session, cleanup_job_params)
