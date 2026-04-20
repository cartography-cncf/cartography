import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.accessgroup import VercelAccessGroupSchema
from cartography.models.vercel.accessgroup import VercelAccessGroupToProjectRel
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    groups = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
    )
    groups, project_assignments = transform_access_groups(groups)
    load_access_groups(
        neo4j_session,
        groups,
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_access_group_project_rels(
        neo4j_session,
        project_assignments,
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_id: str,
) -> list[dict[str, Any]]:
    groups = paginated_get(
        api_session,
        f"{base_url}/v1/access-groups",
        "accessGroups",
        team_id,
    )

    for group in groups:
        group_id = group["accessGroupId"]
        members = paginated_get(
            api_session,
            f"{base_url}/v1/access-groups/{group_id}/members",
            "members",
            team_id,
        )
        group["members"] = members

        projects = paginated_get(
            api_session,
            f"{base_url}/v1/access-groups/{group_id}/projects",
            "projects",
            team_id,
        )
        group["projects"] = projects

    return groups


def transform_access_groups(
    groups: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # Flatten member objects to a list of uids (HAS_MEMBER is loaded via
    # one_to_many on the node), and extract (group, project, role) tuples for
    # HAS_ACCESS_TO rels that carry the per-project role.
    project_assignments: list[dict[str, Any]] = []
    for group in groups:
        members = group.pop("members", []) or []
        group["member_ids"] = [m["uid"] for m in members]

        projects = group.pop("projects", []) or []
        for project in projects:
            project_assignments.append(
                {
                    "accessGroupId": group["accessGroupId"],
                    "projectId": project["projectId"],
                    "role": project.get("role"),
                }
            )
    return groups, project_assignments


@timeit
def load_access_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        VercelAccessGroupSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


@timeit
def load_access_group_project_rels(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        VercelAccessGroupToProjectRel(),
        data,
        lastupdated=update_tag,
        _sub_resource_label="VercelTeam",
        _sub_resource_id=team_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(VercelAccessGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_matchlink(
        VercelAccessGroupToProjectRel(),
        "VercelTeam",
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
