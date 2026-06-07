from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.subimage.team import SubImageTeamMemberSchema
from cartography.util import timeit

_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, common_job_parameters["BASE_URL"])
    members = transform(raw_data)
    load_team_members(neo4j_session, members, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    response = api_session.get(f"{base_url}/api/team/members", timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def transform(raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": member["id"],
            "email": member.get("email"),
            "first_name": member.get("first_name"),
            "last_name": member.get("last_name"),
            "role": member.get("role"),
        }
        for member in raw_data
    ]


@timeit
def load_team_members(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SubImageTeamMemberSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SubImageTeamMemberSchema(), common_job_parameters).run(
        neo4j_session,
    )
