import logging
from typing import Any

import neo4j
from workos import WorkOSClient
from workos.types.roles.role import Role

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.role import WorkOSRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    org_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync WorkOS Roles (environment-level and organization-level).

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param org_ids: List of organization IDs to fetch roles for
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    roles: dict[str, Role] = {}
    for org_id in org_ids:
        roles[org_id] = get(client, org_id)
    transformed_roles = transform(roles)
    load_roles(neo4j_session, transformed_roles, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: WorkOSClient, org_id: str) -> list[dict[str, Any]]:
    """
    Fetch all roles for an organization.

    :param client: WorkOS API client
    :param org_id: Organization ID to fetch roles for
    :return: List of role objects with _org_id attached for organization roles
    """
    logger.debug("Fetching WorkOS environment-level roles")

    # Fetch organization-level roles for each organization
    logger.debug(f"Fetching WorkOS roles for organization: {org_id}")
    return paginated_list(
        client.organizations.list_organization_roles, organization_id=org_id
    )


def transform(roles_by_org: dict[str, list[Role]]) -> list[dict[str, Any]]:
    """
    Transform roles data for loading.
    For OrganizationRole types, adds organization_id from _org_id.

    :param roles_by_org: Raw role objects from WorkOS grouped by organization ID
    :return: Transformed list of role dicts
    """
    result = []

    for org_id, org_roles in roles_by_org.items():
        for role in org_roles:
            role_dict = {
                "id": role.id,
                "slug": role.slug,
                "name": role.name,
                "description": role.description,
                "type": role.type,
                "organization_id": org_id,
                "created_at": role.created_at,
                "updated_at": role.updated_at,
            }
            result.append(role_dict)

    return result


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load roles into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of role dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(f"Loading {len(data)} WorkOS roles into Neo4j")
    load(
        neo4j_session,
        WorkOSRoleSchema(),
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
    Cleanup old roles.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSRoleSchema(),
        common_job_parameters,
    ).run(neo4j_session)
