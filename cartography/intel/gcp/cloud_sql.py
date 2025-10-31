import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudsql.database import GCPSqlDatabaseSchema
from cartography.models.gcp.cloudsql.instance import GCPSqlInstanceSchema
from cartography.models.gcp.cloudsql.user import GCPSqlUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_sql_instances(client: Resource, project_id: str) -> List[Dict]:
    """
    Gets GCP SQL Instances for a project.
    """
    instances: List[Dict] = []
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
    except HttpError:
        logger.warning(
            f"Failed to get SQL instances for project {project_id} due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_sql_databases(
    client: Resource, project_id: str, instance_name: str
) -> List[Dict]:
    """
    Gets SQL Databases for a given Instance.
    """
    databases: List[Dict] = []
    try:
        request = client.databases().list(project=project_id, instance=instance_name)
        response = request.execute()
        databases.extend(response.get("items", []))
        return databases
    except HttpError:
        logger.warning(
            f"Failed to get SQL databases for instance {instance_name} due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_sql_users(client: Resource, project_id: str, instance_name: str) -> List[Dict]:
    """
    Gets SQL Users for a given Instance.
    """
    users: List[Dict] = []
    try:
        request = client.users().list(project=project_id, instance=instance_name)
        response = request.execute()
        users.extend(response.get("items", []))
        return users
    except HttpError:
        logger.warning(
            f"Failed to get SQL users for instance {instance_name} due to a transient HTTP error.",
            exc_info=True,
        )
        return []


def transform_sql_instances(instances_data: List[Dict], project_id: str) -> List[Dict]:
    """
    Transforms the list of SQL Instance dicts for ingestion.
    """
    transformed: List[Dict] = []
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
            }
        )
    return transformed


def transform_sql_databases(databases_data: List[Dict], instance_id: str) -> List[Dict]:
    """
    Transforms the list of SQL Database dicts for ingestion.
    """
    transformed: List[Dict] = []
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
            }
        )
    return transformed


def transform_sql_users(users_data: List[Dict], instance_id: str) -> List[Dict]:
    """
    Transforms the list of SQL User dicts for ingestion.
    """
    transformed: List[Dict] = []
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
            }
        )
    return transformed


@timeit
def load_sql_instances(
    neo4j_session: neo4j.Session, data: List[Dict], project_id: str, update_tag: int
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
def load_sql_databases(
    neo4j_session: neo4j.Session, data: List[Dict], project_id: str, update_tag: int
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
def load_sql_users(
    neo4j_session: neo4j.Session, data: List[Dict], project_id: str, update_tag: int
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
def cleanup_sql(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    """
    Cleans up stale Cloud SQL resources in the graph.
    """
    GraphJob.from_node_schema(GCPSqlDatabaseSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPSqlUserSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPSqlInstanceSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    sql_client: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    The main sync function for GCP Cloud SQL.
    """
    logger.info(f"Syncing GCP Cloud SQL for project {project_id}.")

    # 1. Get Instances
    instances_raw = get_sql_instances(sql_client, project_id)

    if not instances_raw:
        logger.info(f"No Cloud SQL instances found for project {project_id}.")
    else:
        # 2. Transform and Load Instances
        instances = transform_sql_instances(instances_raw, project_id)
        load_sql_instances(neo4j_session, instances, project_id, gcp_update_tag)

        # 3. Get, Transform, and Load children for each instance
        all_databases: List[Dict] = []
        all_users: List[Dict] = []

        for inst in instances_raw:
            instance_name = inst.get("name")
            instance_id = inst.get("selfLink")
            if not instance_name or not instance_id:
                continue

            # Get Databases
            databases_raw = get_sql_databases(sql_client, project_id, instance_name)
            all_databases.extend(transform_sql_databases(databases_raw, instance_id))

            # Get Users
            users_raw = get_sql_users(sql_client, project_id, instance_name)
            all_users.extend(transform_sql_users(users_raw, instance_id))

        # 4. Load all children
        load_sql_databases(neo4j_session, all_databases, project_id, gcp_update_tag)
        load_sql_users(neo4j_session, all_users, project_id, gcp_update_tag)

    # 5. Cleanup
    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_sql(neo4j_session, cleanup_job_params)

    # TODO: create [:PERMISSION_TO] relationships(IAM).

    # TODO: Add the `ENCRYPTED_BY` relationship to the `GCPSqlInstanceSchema` model.
