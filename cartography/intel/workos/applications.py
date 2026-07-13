import json
import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.application import WorkOSApplicationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    common_job_parameters: dict[str, Any],
) -> list[str]:
    """
    Sync WorkOS Connect Applications.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: List of application IDs synced
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    apps = get_applications(client)
    transformed_apps = transform(apps)
    load_applications(neo4j_session, transformed_apps, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return [app["id"] for app in transformed_apps]


@timeit
def get_applications(client: WorkOSClient) -> list[Any]:
    """
    Fetch Connect applications from WorkOS API.

    :param client: WorkOS API client
    :return: List of ConnectApplication objects
    """
    logger.debug("Fetching Connect applications")
    return paginated_list(client.connect.list_applications)


def transform(apps: list[Any]) -> list[dict[str, Any]]:
    """
    Transform Connect application data for loading.

    :param apps: Raw ConnectApplication objects from WorkOS
    :return: Transformed list of application dicts
    """
    logger.debug("Transforming %d WorkOS Connect applications", len(apps))
    result = []

    for app in apps:
        app_dict = {
            "id": app.id,
            "client_id": app.client_id,
            "name": app.name,
            "description": app.description,
            "application_type": app.application_type,
            "organization_id": app.organization_id,
            "scopes": json.dumps(list(app.scopes)) if app.scopes else None,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
        }
        result.append(app_dict)

    return result


@timeit
def load_applications(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load applications into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of application dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    load(
        neo4j_session,
        WorkOSApplicationSchema(),
        data,
        lastupdated=update_tag,
        WORKOS_CLIENT_ID=client_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Cleanup old applications.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSApplicationSchema(),
        common_job_parameters,
    ).run(neo4j_session)
