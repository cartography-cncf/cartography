import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from pagerduty import RestApiV2Client

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.pagerduty.team import PagerDutyTeamSchema
from cartography.models.pagerduty.team_membership import (
    PagerDutyTeamMembershipMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Sub-resource constants for MatchLinks cleanup
SUB_RESOURCE_LABEL = "PagerDutyTeam"


@timeit
def sync_teams(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: RestApiV2Client,
    common_job_parameters: dict[str, Any],
) -> None:
    teams = get_teams(pd_session)
    load_team_data(neo4j_session, teams, update_tag)
    relations = get_team_members(pd_session, teams)
    load_team_memberships(neo4j_session, relations, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_teams(pd_session: RestApiV2Client) -> List[Dict[str, Any]]:
    all_teams: List[Dict[str, Any]] = []
    for teams in pd_session.iter_all("teams"):
        all_teams.append(teams)
    return all_teams


@timeit
def get_team_members(
    pd_session: RestApiV2Client,
    teams: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    relations: List[Dict[str, str]] = []
    for team in teams:
        team_id = team["id"]
        for member in pd_session.iter_all(f"teams/{team_id}/members"):
            relations.append(
                {"team": team_id, "user": member["user"]["id"], "role": member["role"]},
            )
    return relations


def load_team_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load team information
    """
    logger.info(f"Loading {len(data)} pagerduty teams.")
    load(neo4j_session, PagerDutyTeamSchema(), data, lastupdated=update_tag)


def load_team_memberships(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Load team membership relationships using MatchLinks.

    This uses MatchLinks because the MEMBER_OF relationship has a 'role' property
    that varies per user-team pair (e.g., "manager", "responder").
    """
    logger.info(f"Loading {len(data)} pagerduty team memberships.")
    load_matchlinks(
        neo4j_session,
        PagerDutyTeamMembershipMatchLink(),
        data,
        lastupdated=update_tag,
        _sub_resource_label=SUB_RESOURCE_LABEL,
        _sub_resource_id="module",
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # Cleanup stale team nodes
    GraphJob.from_node_schema(PagerDutyTeamSchema(), common_job_parameters).run(
        neo4j_session,
    )
    # Cleanup stale team membership relationships
    GraphJob.from_matchlink(
        PagerDutyTeamMembershipMatchLink(),
        SUB_RESOURCE_LABEL,
        "module",
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
