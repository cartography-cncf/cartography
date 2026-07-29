import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import list_workspace_members
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.workspace_member import ModalWorkspaceMemberSchema
from cartography.models.modal.workspace_role import ModalWorkspaceRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Modal's workspace roles are a fixed builtin set, not API objects, so they are derived
# from the MEMBER_ROLE_* enum rather than listed. MEMBER_ROLE_USER is Modal's name for an
# ordinary member.
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
) -> list[dict[str, Any]]:
    """Ingest workspace members and the builtin workspace roles they hold."""
    raw = await list_workspace_members(client)
    workspace_id = common_job_parameters["WORKSPACE_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    # Roles are loaded first: the member's HAS_ROLE matcher needs the role node to exist.
    roles = transform_roles(workspace_id)
    load_roles(neo4j_session, roles, workspace_id, update_tag)

    members = transform(raw, workspace_id)
    load_members(neo4j_session, members, workspace_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
    return members


def transform_roles(workspace_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{workspace_id}/{name}",
            "name": name,
            "scope": "workspace",
        }
        for name in sorted(_MEMBER_ROLE_NAMES.values())
    ]


def transform(raw: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    members = []
    for member in raw:
        role_name = _MEMBER_ROLE_NAMES.get(member.get("member_role") or "")
        members.append(
            {
                **member,
                # Resolved here so the HAS_ROLE matcher is a plain scalar lookup. Left as
                # None for an unrecognised role, which makes the edge silently absent
                # rather than pointing at a role node that was never created.
                "workspace_role_id": (
                    f"{workspace_id}/{role_name}" if role_name else None
                ),
            }
        )
    return members


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
def load_members(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalWorkspaceMemberSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ModalWorkspaceMemberSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ModalWorkspaceRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
