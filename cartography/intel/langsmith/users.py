import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithPermissionError
from cartography.models.langsmith.orgmembership import LangSmithOrgMembershipSchema
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
    users, org_memberships = transform_users(org_id, active, pending)

    complete = True
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
            complete = False
            continue
        memberships.extend(transform_memberships(workspace_id, workspace_members))

    load_users(
        neo4j_session,
        users,
        org_memberships,
        memberships,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping LangSmith membership cleanup for organization %s: not every "
            "workspace could be read, so existing memberships are preserved.",
            org_id,
        )
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
    org_id: str,
    active: list[dict[str, Any]],
    pending: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Split organization members into shared user identities and per-organization memberships.

    A user can belong to several organizations, so anything organization-specific — the
    identity UUID, whether it is disabled, the organization role, how it was provisioned —
    goes on the membership record. Only identity that is true of the person everywhere
    stays on the user. Writing per-organization state onto a globally keyed user node would
    mean the last organization synced silently overwrites the others.

    Users are keyed on ls_user_id. Pending invitations have not been accepted and therefore
    have no ls_user_id, so they are skipped rather than loaded as half-formed users.
    """
    users: dict[str, dict[str, Any]] = {}
    memberships: list[dict[str, Any]] = []

    for is_pending, members in ((False, active), (True, pending)):
        for member in members:
            ls_user_id = member.get("ls_user_id")
            if not ls_user_id:
                logger.debug(
                    "Skipping pending LangSmith invite for %s: no ls_user_id until accepted.",
                    member.get("email"),
                )
                continue
            providers, provisioning, usernames = _login_methods(member)

            # Later organizations must not clobber identity already seen; the fields here
            # are the same person everywhere, so first non-null wins.
            user = users.setdefault(
                ls_user_id,
                {
                    "ls_user_id": ls_user_id,
                    "email": None,
                    "full_name": None,
                    "display_name": None,
                    "avatar_url": None,
                    "tenant_ids": [],
                    "usernames": [],
                },
            )
            for field in ("email", "full_name", "display_name", "avatar_url"):
                if user[field] is None:
                    user[field] = member.get(field)
            for tenant_id in member.get("tenant_ids") or []:
                if tenant_id not in user["tenant_ids"]:
                    user["tenant_ids"].append(tenant_id)
            for username in usernames:
                if username not in user["usernames"]:
                    user["usernames"].append(username)

            memberships.append(
                {
                    "id": f"{org_id}|{ls_user_id}",
                    "identity_id": member.get("id"),
                    "ls_user_id": ls_user_id,
                    "email": member.get("email"),
                    "role_id": member.get("org_role_id") or member.get("role_id"),
                    "role_name": member.get("org_role_name") or member.get("role_name"),
                    "is_disabled": member.get("is_disabled"),
                    "is_pending": is_pending,
                    "login_methods": providers,
                    "provisioning_methods": provisioning,
                    "created_at": member.get("created_at"),
                }
            )
    return list(users.values()), memberships


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
    org_memberships: list[dict[str, Any]],
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
        LangSmithOrgMembershipSchema(),
        org_memberships,
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
    GraphJob.from_node_schema(
        LangSmithOrgMembershipSchema(), common_job_parameters
    ).run(neo4j_session)
    # LangSmithUser has no sub-resource because a user can span organizations, so this
    # prunes stale relationships without ever deleting a shared identity node.
    GraphJob.from_node_schema(LangSmithUserSchema(), common_job_parameters).run(
        neo4j_session
    )
