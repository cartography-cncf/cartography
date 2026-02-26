import json
import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.directory_group import WorkOSDirectoryGroupSchema
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
    Sync WorkOS Directory Groups.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param directory_ids: List of directory IDs from directories.sync()
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    groups = get(client, directory_ids)
    transformed_groups = transform(groups)
    load_directory_groups(neo4j_session, transformed_groups, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: WorkOSClient, directory_ids: list[str]) -> list[Any]:
    """
    Fetch all directory groups from WorkOS API by iterating over directory IDs.

    :param client: WorkOS API client
    :param directory_ids: List of directory IDs
    :return: List of directory group objects
    """
    logger.debug(
        f"Fetching WorkOS directory groups from {len(directory_ids)} directories"
    )
    all_groups = []

    for directory_id in directory_ids:
        logger.debug(f"Fetching groups for directory: {directory_id}")
        all_groups.extend(
            paginated_list(client.directory_sync.list_groups, directory_id=directory_id)
        )

    logger.debug(f"Fetched {len(all_groups)} directory groups")
    return all_groups


def transform(groups: list[Any]) -> list[dict[str, Any]]:
    """
    Transform directory groups data for loading.

    :param groups: Raw directory group objects from WorkOS
    :return: Transformed list of directory group dicts
    """
    logger.debug(f"Transforming {len(groups)} WorkOS directory groups")
    result = []

    for group in groups:
        group_dict = {
            "id": group.id,
            "idp_id": group.idp_id,
            "directory_id": group.directory_id,
            "organization_id": group.organization_id,
            "name": group.name,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "raw_attributes": (
                json.dumps(group.raw_attributes) if group.raw_attributes else None
            ),
        }

        result.append(group_dict)

    return result


@timeit
def load_directory_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load directory groups into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of directory group dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(f"Loading {len(data)} WorkOS directory groups into Neo4j")
    load(
        neo4j_session,
        WorkOSDirectoryGroupSchema(),
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
    Cleanup old directory groups.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSDirectoryGroupSchema(),
        common_job_parameters,
    ).run(neo4j_session)
