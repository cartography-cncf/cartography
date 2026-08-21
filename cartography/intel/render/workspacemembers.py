import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_plain_array
from cartography.intel.render.util import require_non_empty
from cartography.models.render.workspacemember import RenderWorkspaceMemberSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, owner_id: str) -> list[dict[str, Any]]:
    # No pagination params are documented for this endpoint - see list_plain_array()'s
    # docstring for why bare-array endpoints only ever make a single GET.
    return list_plain_array(session, f"{BASE_URL}/owners/{owner_id}/members")


def transform(members: list[dict[str, Any]], owner_id: str) -> list[dict[str, Any]]:
    """
    id is scoped per-workspace-membership (`<owner id>:<user id>`), not bare userId -
    see RenderWorkspaceMemberNodeProperties' docstring for why.
    """
    return [
        {
            "id": f"{owner_id}:{require_non_empty(member.get('userId'), 'member user id')}",
            "userId": member.get("userId"),
            "name": member.get("name"),
            "email": member.get("email"),
            "ownerId": owner_id,
            "status": member.get("status"),
            "role": member.get("role"),
            "mfaEnabled": member.get("mfaEnabled"),
        }
        for member in members
    ]


@timeit
def load_workspace_members(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderWorkspaceMemberSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderWorkspaceMemberSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    members = get(session, owner_id)
    transformed = transform(members, owner_id)
    load_workspace_members(neo4j_session, transformed, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
