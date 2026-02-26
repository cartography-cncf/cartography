import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.organization import WorkOSOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    common_job_parameters: dict[str, Any],
) -> list[str]:
    """
    Sync WorkOS Organizations.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: list of organization IDs
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    organizations = get(client)
    transformed_orgs = transform(organizations)
    load_organizations(neo4j_session, transformed_orgs, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return [org["id"] for org in transformed_orgs]


@timeit
def get(client: WorkOSClient) -> list[dict[str, Any]]:
    """
    Fetch all organizations from WorkOS API.

    :param client: WorkOS API client
    :return: list of organization dicts
    """
    logger.debug("Fetching WorkOS organizations")
    return paginated_list(client.organizations.list_organizations)


def transform(organizations: list[Any]) -> list[dict[str, Any]]:
    """
    Transform organizations data for loading.

    :param organizations: Raw organization objects from WorkOS
    :return: Transformed list of organization dicts
    """
    logger.debug(f"Transforming {len(organizations)} WorkOS organizations")
    result = []

    for org in organizations:
        org_dict = {
            "id": org.id,
            "name": org.name,
            "created_at": org.created_at,
            "updated_at": org.updated_at,
            "allow_profiles_outside_organization": org.allow_profiles_outside_organization,
        }
        result.append(org_dict)

    return result


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load organizations into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: list of organization dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(f"Loading {len(data)} WorkOS organizations into Neo4j")
    load(
        neo4j_session,
        WorkOSOrganizationSchema(),
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
    Cleanup old organizations.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSOrganizationSchema(),
        common_job_parameters,
    ).run(neo4j_session)
