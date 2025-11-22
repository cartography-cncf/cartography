import logging
from typing import Any

import neo4j
from slack_sdk import WebClient

from cartography.client.core.tx import load
from cartography.models.slack.team import SlackTeamSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    slack_client: WebClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[str]:
    # If no team ID is provided, we fetch the team info for the authenticated team
    if not common_job_parameters.get("TEAM_ID"):
        teams = get_teams(slack_client)
        team_ids = [t["id"] for t in teams.get("teams", [])]
    else:
        team_ids = [common_job_parameters["TEAM_ID"]]
    teams_details = get_teams_details(slack_client, team_ids)
    load_team(neo4j_session, teams_details, update_tag)

    return team_ids


@timeit
def get_teams(slack_client: WebClient) -> dict[str, Any]:
    response = slack_client.auth_teams_list()
    return response.data


@timeit
def get_teams_details(
    slack_client: WebClient, teams_ids: list[str]
) -> list[dict[str, Any]]:
    # Get teams
    teams: list[dict[str, Any]] = []
    for team_id in teams_ids:
        response = slack_client.team_info(team=team_id)
        team = response.data.get("team")
        if team:
            teams.append(team)
    return teams


@timeit
def load_team(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %s Slack teams into Neo4j", len(data))
    load(
        neo4j_session,
        SlackTeamSchema(),
        data,
        lastupdated=update_tag,
    )
