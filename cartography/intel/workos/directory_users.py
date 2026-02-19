import json
import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.directory_user import WorkOSDirectoryUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    directory_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync WorkOS Directory Users.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param directory_ids: List of directory IDs from directories.sync()
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    users = get(client, directory_ids)
    transformed_users = transform(users)
    load_directory_users(neo4j_session, transformed_users, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: WorkOSClient, directory_ids: list[str]) -> list[dict[str, Any]]:
    """
    Fetch all directory users from WorkOS API by iterating over directory IDs.

    :param client: WorkOS API client
    :param directory_ids: List of directory IDs
    :return: List of directory user dicts
    """
    logger.debug(
        f"Fetching WorkOS directory users from {len(directory_ids)} directories"
    )
    all_users = []

    for directory_id in directory_ids:
        logger.debug(f"Fetching users for directory: {directory_id}")
        all_users.extend(
            paginated_list(client.directory_sync.list_users, directory_id=directory_id)
        )

    logger.debug(f"Fetched {len(all_users)} directory users")
    return all_users


def transform(users: list[Any]) -> list[dict[str, Any]]:
    """
    Transform directory users data for loading.

    :param users: Raw directory user objects from WorkOS
    :return: Transformed list of directory user dicts
    """
    logger.debug(f"Transforming {len(users)} WorkOS directory users")
    result = []

    for user in users:
        user_dict = {
            "id": user.id,
            "idp_id": user.idp_id,
            "directory_id": user.directory_id,
            "organization_id": user.organization_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "group_ids": [g.id for g in user.groups],
            "state": user.state,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "custom_attributes": (
                json.dumps(user.custom_attributes) if user.custom_attributes else None
            ),
            "raw_attributes": (
                json.dumps(user.raw_attributes) if user.raw_attributes else None
            ),
            "role": user.role.slug if user.role else None,
        }

        result.append(user_dict)

    return result


@timeit
def load_directory_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load directory users into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of directory user dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(f"Loading {len(data)} WorkOS directory users into Neo4j")
    load(
        neo4j_session,
        WorkOSDirectoryUserSchema(),
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
    Cleanup old directory users.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSDirectoryUserSchema(),
        common_job_parameters,
    ).run(neo4j_session)
