import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.pylon.util import paginated_get
from cartography.models.pylon.team import PylonTeamSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_teams = get(api_session, base_url)
    teams = transform(raw_teams)
    load_teams(
        neo4j_session,
        teams,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return paginated_get(api_session, f"{base_url}/teams")


def transform(raw_teams: list[dict[str, Any]]) -> list[dict[str, Any]]:
    teams = []
    for team in raw_teams:
        assignment = team.get("assignment_configuration") or {}
        teams.append(
            {
                "id": team["id"],
                "name": team.get("name"),
                "assignment_method": assignment.get("assignment_method"),
                "member_ids": sorted(
                    {member["id"] for member in team.get("users") or []},
                ),
            },
        )
    return teams


@timeit
def load_teams(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Pylon teams for organization %s", len(data), org_id)
    load(
        neo4j_session,
        PylonTeamSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(PylonTeamSchema(), common_job_parameters).run(
        neo4j_session,
    )
