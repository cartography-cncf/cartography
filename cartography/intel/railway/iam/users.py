import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.railway.iam.project_membership import (
    RailwayUserToProjectMatchLink,
)
from cartography.models.railway.iam.user import RailwayUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    workspace: dict[str, Any],
    projects: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load workspace members and their per-project memberships.

    Both come from data already fetched by the projects sync, so this makes no request of
    its own.
    """
    workspace_id = common_job_parameters["WORKSPACE_ID"]

    users = transform_users(workspace, projects)
    memberships = transform_project_memberships(projects)

    load_users(neo4j_session, users, workspace_id, update_tag)
    load_project_memberships(neo4j_session, memberships, workspace_id, update_tag)
    cleanup(neo4j_session, common_job_parameters, workspace_id, update_tag)


def transform_users(
    workspace: dict[str, Any],
    projects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Merge workspace members with project members.

    On Team plans a project member is not necessarily a workspace member, so both sources
    are unioned. Workspace records win on conflict: they carry twoFactorAuthEnabled, which
    the project member payload does not include.
    """
    users: dict[str, dict[str, Any]] = {}
    for project in projects:
        for member in project.get("members") or []:
            users[member["id"]] = {
                "id": member["id"],
                "email": member.get("email"),
                "name": member.get("name"),
                "twoFactorAuthEnabled": None,
                # A project role is not a workspace role; it lives on the MatchLink instead.
                "role": None,
            }
    for member in workspace.get("members") or []:
        users[member["id"]] = {
            "id": member["id"],
            "email": member.get("email"),
            "name": member.get("name"),
            "twoFactorAuthEnabled": member.get("twoFactorAuthEnabled"),
            "role": member.get("role"),
        }
    return list(users.values())


def transform_project_memberships(
    projects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    memberships = []
    for project in projects:
        for member in project.get("members") or []:
            memberships.append(
                {
                    "user_id": member["id"],
                    "project_id": project["id"],
                    "role": member.get("role"),
                },
            )
    return memberships


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RailwayUserSchema(),
        users,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def load_project_memberships(
    neo4j_session: neo4j.Session,
    memberships: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        RailwayUserToProjectMatchLink(),
        memberships,
        lastupdated=update_tag,
        _sub_resource_label="RailwayWorkspace",
        _sub_resource_id=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    workspace_id: str,
    update_tag: int,
) -> None:
    GraphJob.from_matchlink(
        RailwayUserToProjectMatchLink(),
        "RailwayWorkspace",
        workspace_id,
        update_tag,
    ).run(neo4j_session)
    GraphJob.from_node_schema(RailwayUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
