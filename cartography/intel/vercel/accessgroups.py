import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import _TIMEOUT
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.accessgroup import VercelAccessGroupSchema
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
    load_access_groups(
        neo4j_session,
        groups,
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
        members_resp = api_session.get(
            f"{base_url}/v1/access-groups/{group_id}/members",
            params={"teamId": team_id, "limit": "100"},
            timeout=_TIMEOUT,
        )
        members_resp.raise_for_status()
        group["member_ids"] = [m["uid"] for m in members_resp.json().get("members", [])]

        projects_resp = api_session.get(
            f"{base_url}/v1/access-groups/{group_id}/projects",
            params={"teamId": team_id, "limit": "100"},
            timeout=_TIMEOUT,
        )
        projects_resp.raise_for_status()
        group["project_ids"] = [
            p["projectId"] for p in projects_resp.json().get("projects", [])
        ]

    return groups


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
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(VercelAccessGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )
