import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.organization_membership import (
    WorkOSOrganizationMembershipSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    org_ids: list[str],
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync WorkOS Organization Memberships as nodes.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    memberships = get(client, org_ids)
    transformed_memberships = transform(memberships)
    load_organization_memberships(
        neo4j_session, transformed_memberships, client_id, update_tag
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: WorkOSClient, org_ids: list[str]) -> List[Dict[str, Any]]:
    """
    Fetch all organization memberships from WorkOS API.

    :param client: WorkOS API client
    :return: List of organization membership dicts
    """
    result = []
    logger.debug("Fetching WorkOS organization memberships")
    for org_id in org_ids:
        result.extend(
            paginated_list(
                client.user_management.list_organization_memberships,
                organization_id=org_id,
            )
        )
    return result


def transform(memberships: list[Any]) -> list[dict[str, Any]]:
    """
    Transform organization memberships data for loading.
    Extract role id from role object and generate unique ID.

    :param memberships: Raw organization membership objects from WorkOS
    :return: Transformed list of organization membership dicts
    """
    logger.debug(f"Transforming {len(memberships)} WorkOS organization memberships")
    result = []

    for membership in memberships:

        membership_dict = {
            "id": membership.id,
            "user_id": membership.user_id,
            "organization_id": membership.organization_id,
            "status": membership.status,
            "created_at": getattr(membership, "created_at", None),
            "updated_at": getattr(membership, "updated_at", None),
            "roles": [r["slug"] for r in membership.roles],
        }

        result.append(membership_dict)

    return result


@timeit
def load_organization_memberships(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load organization memberships as nodes into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of organization membership dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(
        f"Loading {len(data)} WorkOS organization memberships as nodes into Neo4j"
    )
    load(
        neo4j_session,
        WorkOSOrganizationMembershipSchema(),
        data,
        lastupdated=update_tag,
        WORKOS_CLIENT_ID=client_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Cleanup old organization membership nodes.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSOrganizationMembershipSchema(),
        common_job_parameters,
    ).run(neo4j_session)
