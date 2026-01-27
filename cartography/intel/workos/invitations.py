import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.invitation import WorkOSInvitationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync WorkOS Invitations.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    invitations = get(client)
    transformed_invitations = transform(invitations)
    load_invitations(neo4j_session, transformed_invitations, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: WorkOSClient) -> list[dict[str, Any]]:
    """
    Fetch all invitations from WorkOS API.

    :param client: WorkOS API client
    :return: List of invitation dicts
    """
    logger.debug("Fetching WorkOS invitations")
    return paginated_list(client.user_management.list_invitations)


def transform(invitations: list[Any]) -> list[dict[str, Any]]:
    """
    Transform invitations data for loading.

    :param invitations: Raw invitation objects from WorkOS
    :return: Transformed list of invitation dicts
    """
    logger.debug(f"Transforming {len(invitations)} WorkOS invitations")
    result = []

    for invitation in invitations:
        invitation_dict = {
            "id": invitation.id,
            "email": invitation.email,
            "state": invitation.state,
            "organization_id": invitation.organization_id,
            "inviter_user_id": invitation.inviter_user_id,
            "token": getattr(invitation, "token", None),
            "accept_invitation_url": getattr(invitation, "accept_invitation_url", None),
            "expires_at": invitation.expires_at,
            "created_at": invitation.created_at,
            "updated_at": invitation.updated_at,
            "accepted_at": invitation.accepted_at,
            "revoked_at": getattr(invitation, "revoked_at", None),
        }
        result.append(invitation_dict)

    return result


@timeit
def load_invitations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load invitations into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of invitation dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(f"Loading {len(data)} WorkOS invitations into Neo4j")
    load(
        neo4j_session,
        WorkOSInvitationSchema(),
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
    Cleanup old invitations.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSInvitationSchema(),
        common_job_parameters,
    ).run(neo4j_session)
