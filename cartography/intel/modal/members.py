import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import list_workspace_members
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.user import ModalUserMemberOfWorkspaceMatchLink
from cartography.models.modal.user import ModalUserSchema
from cartography.models.modal.user import ModalUserToWorkspaceRoleMatchLink
from cartography.models.modal.workspace_role import ModalWorkspaceRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Modal's workspace roles are a fixed builtin set, not API objects, so they are derived from
# the MEMBER_ROLE_* enum rather than listed. MEMBER_ROLE_USER is Modal's name for an ordinary
# member.
_MEMBER_ROLE_NAMES = {
    "MEMBER_ROLE_USER": "member",
    "MEMBER_ROLE_MANAGER": "manager",
    "MEMBER_ROLE_OWNER": "owner",
}


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
) -> dict[str, str]:
    """Ingest the workspace's users, their memberships and the builtin workspace roles.

    Returns a ``{display_name: user_id}`` map for this workspace, which the callers that need
    to attribute object creation use to resolve Modal's username-only ``created_by`` into a
    ModalUser id.
    """
    raw = await list_workspace_members(client)
    workspace_id = common_job_parameters["WORKSPACE_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    # Roles first: the HAS_ROLE MatchLink needs its target node to exist.
    roles = transform_roles(workspace_id)
    load_roles(neo4j_session, roles, workspace_id, update_tag)

    users = transform(raw)
    load_users(neo4j_session, users, update_tag)

    memberships = transform_memberships(raw, workspace_id)
    load_memberships(neo4j_session, memberships, workspace_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
    return user_ids_by_username(users)


def transform_roles(workspace_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{workspace_id}/{name}",
            "name": name,
            "scope": "workspace",
        }
        for name in sorted(_MEMBER_ROLE_NAMES.values())
    ]


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only the person-level fields, which are the same in every workspace."""
    return [
        {
            "id": member["id"],
            "email": member.get("email"),
            "display_name": member.get("display_name"),
            "identity_provider_type": member.get("identity_provider_type"),
            "idp_external_id": member.get("idp_external_id"),
            "avatar_url": member.get("avatar_url"),
        }
        for member in raw
    ]


def transform_memberships(
    raw: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    """Build the per-workspace membership rows, one per user.

    ``workspace_role_id`` is resolved here so the HAS_ROLE matcher is a plain scalar lookup. It
    is left None for an unrecognised role, which makes the edge silently absent rather than
    pointing at a role node that was never created.
    """
    memberships = []
    for member in raw:
        role_name = _MEMBER_ROLE_NAMES.get(member.get("member_role") or "")
        memberships.append(
            {
                "user_id": member["id"],
                "workspace_id": workspace_id,
                "member_id": member.get("member_id"),
                "member_role": member.get("member_role"),
                "joined_at": member.get("joined_at"),
                "last_active_at": member.get("last_active_at"),
                "deleted_at": member.get("deleted_at"),
                "workspace_role_id": (
                    f"{workspace_id}/{role_name}" if role_name else None
                ),
            }
        )
    return memberships


def user_ids_by_username(users: list[dict[str, Any]]) -> dict[str, str]:
    """Map display name to user id for this workspace.

    Modal attributes object creation by workspace username, and the display name is that
    username. Built per workspace, so a name collision across workspaces cannot leak.
    """
    return {
        user["display_name"]: user["id"] for user in users if user.get("display_name")
    }


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalWorkspaceRoleSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    # No workspace kwarg: ModalUser is a shared identity with no sub-resource.
    load(neo4j_session, ModalUserSchema(), data, lastupdated=update_tag)


@timeit
def load_memberships(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    if not data:
        return
    load_matchlinks(
        neo4j_session,
        ModalUserMemberOfWorkspaceMatchLink(),
        data,
        lastupdated=update_tag,
        _sub_resource_label="ModalWorkspace",
        _sub_resource_id=workspace_id,
    )
    with_role = [row for row in data if row.get("workspace_role_id")]
    if with_role:
        load_matchlinks(
            neo4j_session,
            ModalUserToWorkspaceRoleMatchLink(),
            with_role,
            lastupdated=update_tag,
            _sub_resource_label="ModalWorkspace",
            _sub_resource_id=workspace_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """Clean up the memberships and roles, never the user nodes.

    ModalUser has no sub-resource, so there is no workspace-scoped way to delete one without
    risking another workspace's data. A user who left every workspace therefore lingers as a
    node with no MEMBER_OF edge. See the ModalUser module docstring.
    """
    workspace_id = common_job_parameters["WORKSPACE_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]
    for matchlink in (
        ModalUserToWorkspaceRoleMatchLink(),
        ModalUserMemberOfWorkspaceMatchLink(),
    ):
        GraphJob.from_matchlink(
            matchlink, "ModalWorkspace", workspace_id, update_tag
        ).run(neo4j_session)
    GraphJob.from_node_schema(ModalWorkspaceRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
