import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.directory import WorkOSDirectorySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    common_job_parameters: dict[str, Any],
) -> list[str]:
    """
    Sync WorkOS Directories and return the list of IDs for use by directory_users and directory_groups.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: List of directory IDs
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    directories = get(client)
    transformed_dirs = transform(directories)
    load_directories(neo4j_session, transformed_dirs, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)

    # Return only the IDs
    return [d["id"] for d in transformed_dirs]


@timeit
def get(client: WorkOSClient) -> list[dict[str, Any]]:
    """
    Fetch all directories from WorkOS API.

    :param client: WorkOS API client
    :return: List of directory dicts
    """
    logger.debug("Fetching WorkOS directories")
    return paginated_list(client.directory_sync.list_directories)


def transform(directories: list[Any]) -> list[dict[str, Any]]:
    """
    Transform directories data for loading.

    :param directories: Raw directory objects from WorkOS
    :return: Transformed list of directory dicts
    """
    logger.debug(f"Transforming {len(directories)} WorkOS directories")
    result = []

    for directory in directories:
        dir_dict = {
            "id": directory.id,
            "name": directory.name,
            "domain": directory.domain,
            "state": directory.state,
            "type": directory.type,
            "organization_id": directory.organization_id,
            "created_at": directory.created_at,
            "updated_at": directory.updated_at,
        }
        result.append(dir_dict)

    return result


@timeit
def load_directories(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load directories into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of directory dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(f"Loading {len(data)} WorkOS directories into Neo4j")
    load(
        neo4j_session,
        WorkOSDirectorySchema(),
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
    Cleanup old directories.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSDirectorySchema(),
        common_job_parameters,
    ).run(neo4j_session)
