import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithPermissionError
from cartography.models.langsmith.user import LangSmithUserSchema
from cartography.models.langsmith.workspacemembership import (
    LangSmithWorkspaceMembershipSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    workspace_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    active = get_active_members(client, org_id)
    pending = get_pending_members(client, org_id)
    users = transform_users(active, pending)

    memberships: list[dict[str, Any]] = []
    for workspace_id in workspace_ids:
        try:
            workspace_members = get_workspace_members(client, org_id, workspace_id)
        except LangSmithPermissionError as err:
            # A credential commonly holds workspaces:read in only some workspaces.
            logger.warning(
                "Skipping LangSmith workspace members for workspace %s: %s",
                workspace_id,
                err,
            )
            continue
        memberships.extend(transform_memberships(workspace_id, workspace_members))

    load_users(
        neo4j_session, users, memberships, org_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
    return users


@timeit
def get_active_members(client: LangSmithClient, org_id: str) -> list[dict[str, Any]]:
    return client.get_paginated(
        "/api/v1/orgs/current/members/active",
        org_id=org_id,
    )


@timeit
def get_pending_members(client: LangSmithClient, org_id: str) -> list[dict[str, Any]]:
    return client.get_paginated(
        "/api/v1/orgs/current/members/pending",
        org_id=org_id,
    )


@timeit
def get_workspace_members(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> dict[str, Any]:
    return client.get(
        "/api/v1/workspaces/current/members",
        org_id=org_id,
        tenant_id=workspace_id,
    )


def _login_methods(member: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    providers = []
    provisioning = []
    usernames = []
    for method in member.get("linked_login_methods") or []:
        if method.get("provider"):
            providers.append(method["provider"])
        if method.get("provisioning_method"):
            provisioning.append(method["provisioning_method"])
        if method.get("username"):
            usernames.append(method["username"])
    return sorted(set(providers)), sorted(set(provisioning)), sorted(set(usernames))


def transform_users(
    active: list[dict[str, Any]],
    pending: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Shape organization members for ingest.

    Users are keyed on ls_user_id, the stable LangSmith user identifier. The member row's
    own id is an identity (membership) UUID and is kept as org_identity_id so it is not
    mistaken for a user id. Pending invitations have not been accepted and therefore have no
    ls_user_id, so they are skipped rather than loaded as half-formed users.
    """
    transformed = []
    for member in active:
        providers, provisioning, usernames = _login_methods(member)
        transformed.append(
            {
                "ls_user_id": member["ls_user_id"],
                "org_identity_id": member["id"],
                "email": member.get("email"),
                "full_name": member.get("full_name"),
                "display_name": member.get("display_name"),
                "avatar_url": member.get("avatar_url"),
                "is_disabled": member.get("is_disabled"),
                "is_pending": False,
                "login_methods": providers,
                "provisioning_methods": provisioning,
                "usernames": usernames,
                "org_role_id": member.get("org_role_id") or member.get("role_id"),
                "org_role_name": member.get("org_role_name") or member.get("role_name"),
                "tenant_ids": member.get("tenant_ids") or [],
                "created_at": member.get("created_at"),
            }
        )

    for member in pending:
        if not member.get("ls_user_id"):
            logger.debug(
                "Skipping pending LangSmith invite for %s: no ls_user_id until accepted.",
                member.get("email"),
            )
            continue
        providers, provisioning, usernames = _login_methods(member)
        transformed.append(
            {
                "ls_user_id": member["ls_user_id"],
                "org_identity_id": member.get("id"),
                "email": member.get("email"),
                "full_name": member.get("full_name"),
                "display_name": member.get("display_name"),
                "avatar_url": member.get("avatar_url"),
                "is_disabled": member.get("is_disabled"),
                "is_pending": True,
                "login_methods": providers,
                "provisioning_methods": provisioning,
                "usernames": usernames,
                "org_role_id": member.get("org_role_id") or member.get("role_id"),
                "org_role_name": member.get("org_role_name") or member.get("role_name"),
                "tenant_ids": member.get("tenant_ids") or [],
                "created_at": member.get("created_at"),
            }
        )
    return transformed


def transform_memberships(
    workspace_id: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Flatten a workspace's member listing into (user, workspace, role) membership records.

    A membership is modelled as its own node because LangSmith supports organization-defined
    custom roles, so the role held in a workspace cannot be encoded as a fixed relationship
    label.
    """
    memberships = []
    for is_pending, members in (
        (False, payload.get("members") or []),
        (True, payload.get("pending") or []),
    ):
        for member in members:
            ls_user_id = member.get("ls_user_id")
            if not ls_user_id:
                logger.debug(
                    "Skipping LangSmith workspace membership for %s in workspace %s: "
                    "no ls_user_id until the invite is accepted.",
                    member.get("email"),
                    workspace_id,
                )
                continue
            memberships.append(
                {
                    "id": f"{ls_user_id}|{workspace_id}",
                    "identity_id": member.get("id"),
                    "ls_user_id": ls_user_id,
                    "workspace_id": workspace_id,
                    "email": member.get("email"),
                    "role_id": member.get("role_id"),
                    "role_name": member.get("role_name"),
                    "is_disabled": member.get("is_disabled"),
                    "is_pending": is_pending,
                    "created_at": member.get("created_at"),
                }
            )
    return memberships


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    memberships: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LangSmithUserSchema(),
        users,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load(
        neo4j_session,
        LangSmithWorkspaceMembershipSchema(),
        memberships,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        LangSmithWorkspaceMembershipSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(LangSmithUserSchema(), common_job_parameters).run(
        neo4j_session
    )
