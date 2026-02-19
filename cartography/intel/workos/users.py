import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.user import WorkOSUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync WorkOS Users.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    users = get(client)
    transformed_users = transform(users)
    load_users(neo4j_session, transformed_users, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: WorkOSClient) -> list[dict[str, Any]]:
    """
    Fetch all users from WorkOS API.

    :param client: WorkOS API client
    :return: List of user dicts
    """
    logger.debug("Fetching WorkOS users")
    return paginated_list(client.user_management.list_users)


def transform(users: list[Any]) -> list[dict[str, Any]]:
    """
    Transform users data for loading.

    :param users: Raw user objects from WorkOS
    :return: Transformed list of user dicts
    """
    logger.debug(f"Transforming {len(users)} WorkOS users")
    result = []

    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email_verified": user.email_verified,
            "profile_picture_url": user.profile_picture_url,
            "last_sign_in_at": user.last_sign_in_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
        result.append(user_dict)

    return result


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load users into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of user dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(f"Loading {len(data)} WorkOS users into Neo4j")
    load(
        neo4j_session,
        WorkOSUserSchema(),
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
    Cleanup old users.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSUserSchema(),
        common_job_parameters,
    ).run(neo4j_session)
