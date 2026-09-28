import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.railway.iam.project_membership import (
    RailwayUserToProjectMatchLink,
)
from cartography.models.railway.iam.user import RailwayProjectMemberUserSchema
from cartography.models.railway.iam.user import RailwayUserMemberOfWorkspaceMatchLink
from cartography.models.railway.iam.user import RailwayUserSchema
from cartography.models.railway.iam.user import RailwayUserToWorkspaceMatchLink
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

    workspace_members, project_only_members = transform_users(workspace, projects)
    memberships = transform_project_memberships(projects)

    load_users(
        neo4j_session,
        workspace_members,
        project_only_members,
        workspace_id,
        update_tag,
    )
    load_project_memberships(neo4j_session, memberships, workspace_id, update_tag)
    cleanup(neo4j_session, workspace_id, update_tag)


def transform_users(
    workspace: dict[str, Any],
    projects: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Split members by where Railway reports them.

    On Team plans a project member is not necessarily a workspace member, and the project
    payload carries neither a workspace role nor a 2FA flag. The two groups are therefore
    kept apart and loaded through different schemas, so that a project-only member is never
    asserted to be a member of the workspace.

    :return: (workspace members, members seen only through a project)
    """
    workspace_members = [
        {
            "id": member["id"],
            "email": member.get("email"),
            "name": member.get("name"),
            "twoFactorAuthEnabled": member.get("twoFactorAuthEnabled"),
            "role": member.get("role"),
        }
        for member in workspace.get("members") or []
    ]
    workspace_member_ids = {member["id"] for member in workspace_members}

    project_only_members: dict[str, dict[str, Any]] = {}
    for project in projects:
        for member in project.get("members") or []:
            if member["id"] in workspace_member_ids:
                continue
            project_only_members[member["id"]] = {
                "id": member["id"],
                "email": member.get("email"),
                "name": member.get("name"),
            }

    return workspace_members, list(project_only_members.values())


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
    workspace_members: list[dict[str, Any]],
    project_only_members: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RailwayUserSchema(),
        workspace_members,
        lastupdated=update_tag,
    )
    load(
        neo4j_session,
        RailwayProjectMemberUserSchema(),
        project_only_members,
        lastupdated=update_tag,
    )

    # Both workspace edges are MatchLinks so their cleanup is scoped to this workspace. A
    # node-schema relationship cleanup would match every workspace's edges at once.
    all_members = workspace_members + project_only_members
    load_matchlinks(
        neo4j_session,
        RailwayUserToWorkspaceMatchLink(),
        [
            {"user_id": member["id"], "workspace_id": workspace_id}
            for member in all_members
        ],
        lastupdated=update_tag,
        _sub_resource_label="RailwayWorkspace",
        _sub_resource_id=workspace_id,
    )
    load_matchlinks(
        neo4j_session,
        RailwayUserMemberOfWorkspaceMatchLink(),
        [
            {
                "user_id": member["id"],
                "workspace_id": workspace_id,
                "role": member.get("role"),
            }
            for member in workspace_members
        ],
        lastupdated=update_tag,
        _sub_resource_label="RailwayWorkspace",
        _sub_resource_id=workspace_id,
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
    workspace_id: str,
    update_tag: int,
) -> None:
    # Every edge is a MatchLink, so each job deletes only the stale edges belonging to the
    # workspace being synced and cannot touch another workspace's memberships. The
    # RailwayUser node itself is never cleaned up: it is a shared identity that other
    # workspaces, and other modules, may still reference.
    for matchlink in (
        RailwayUserToProjectMatchLink(),
        RailwayUserMemberOfWorkspaceMatchLink(),
        RailwayUserToWorkspaceMatchLink(),
    ):
        GraphJob.from_matchlink(
            matchlink,
            "RailwayWorkspace",
            workspace_id,
            update_tag,
        ).run(neo4j_session)
