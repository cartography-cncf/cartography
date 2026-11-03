import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.opsgenie.account import OpsgenieAccountSchema
from cartography.models.opsgenie.schedule import OpsgenieScheduleSchema
from cartography.models.opsgenie.team import OpsgenieTeamSchema
from cartography.models.opsgenie.user import OpsgenieUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _get_data(
    api_session: requests.Session,
    url: str,
    timeout: int,
    **params: Any,
) -> dict[str, Any]:
    response = api_session.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


@timeit
def get_account(
    api_session: requests.Session,
    base_url: str,
    timeout: int,
) -> dict[str, Any]:
    return _get_data(api_session, f"{base_url}/v2/account", timeout)["data"]


@timeit
def get_teams(
    api_session: requests.Session,
    base_url: str,
    timeout: int,
) -> list[dict[str, Any]]:
    return _get_data(api_session, f"{base_url}/v2/teams", timeout)["data"]


@timeit
def get_team_members(
    api_session: requests.Session,
    base_url: str,
    timeout: int,
    team_id: str,
) -> list[dict[str, Any]]:
    # The list endpoint omits members, so membership needs one call per team.
    team = _get_data(api_session, f"{base_url}/v2/teams/{team_id}", timeout)["data"]
    return team.get("members") or []


@timeit
def get_users(
    api_session: requests.Session,
    base_url: str,
    timeout: int,
) -> list[dict[str, Any]]:
    users: list[dict[str, Any]] = []
    while True:
        page = _get_data(
            api_session,
            f"{base_url}/v2/users",
            timeout,
            limit=100,
            offset=len(users),
        )
        users.extend(page["data"])
        if len(users) >= page["totalCount"] or not page["data"]:
            return users


@timeit
def get_schedules(
    api_session: requests.Session,
    base_url: str,
    timeout: int,
) -> list[dict[str, Any]]:
    return _get_data(api_session, f"{base_url}/v2/schedules", timeout)["data"]


def transform_account(account: dict[str, Any]) -> list[dict[str, Any]]:
    plan = account.get("plan") or {}
    return [
        {
            "id": account["name"],
            "name": account["name"],
            "user_count": account.get("userCount"),
            "plan_name": plan.get("name"),
            "max_user_count": plan.get("maxUserCount"),
        },
    ]


def transform_teams(teams: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": team["id"],
            "name": team["name"],
            "description": team.get("description"),
        }
        for team in teams
    ]


def transform_users(
    users: list[dict[str, Any]],
    team_members: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    team_ids: dict[str, list[str]] = {}
    for team_id, members in team_members.items():
        for member in members:
            user_id = (member.get("user") or {}).get("id")
            if not user_id:
                continue
            team_ids.setdefault(user_id, []).append(team_id)

    result = []
    for user in users:
        role = user.get("role") or {}
        result.append(
            {
                "id": user["id"],
                "username": user["username"],
                "full_name": user.get("fullName"),
                "role": role.get("name"),
                "blocked": user.get("blocked"),
                "verified": user.get("verified"),
                "timezone": user.get("timeZone"),
                "locale": user.get("locale"),
                "created_at": user.get("createdAt"),
                "team_ids": team_ids.get(user["id"], []),
            },
        )
    return result


def transform_schedules(schedules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for schedule in schedules:
        owner_team = schedule.get("ownerTeam") or {}
        result.append(
            {
                "id": schedule["id"],
                "name": schedule["name"],
                "description": schedule.get("description"),
                "timezone": schedule.get("timezone"),
                "enabled": schedule.get("enabled"),
                "owner_team_id": owner_team.get("id"),
            },
        )
    return result


def _load_and_cleanup(
    neo4j_session: neo4j.Session,
    schema: OpsgenieTeamSchema | OpsgenieUserSchema | OpsgenieScheduleSchema,
    data: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        schema,
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=common_job_parameters["ACCOUNT_ID"],
    )
    GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    timeout: int,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting Opsgenie sync")
    account = transform_account(get_account(api_session, base_url, timeout))
    account_job_parameters = {**common_job_parameters, "ACCOUNT_ID": account[0]["id"]}
    logger.debug("Loading Opsgenie account")
    load(
        neo4j_session,
        OpsgenieAccountSchema(),
        account,
        lastupdated=update_tag,
    )

    raw_teams = get_teams(api_session, base_url, timeout)
    teams = transform_teams(raw_teams)
    logger.debug("Loading %d Opsgenie teams", len(teams))
    _load_and_cleanup(
        neo4j_session,
        OpsgenieTeamSchema(),
        teams,
        update_tag,
        account_job_parameters,
    )

    team_members = {
        team["id"]: get_team_members(api_session, base_url, timeout, team["id"])
        for team in raw_teams
    }
    users = transform_users(get_users(api_session, base_url, timeout), team_members)
    logger.debug("Loading %d Opsgenie users", len(users))
    _load_and_cleanup(
        neo4j_session,
        OpsgenieUserSchema(),
        users,
        update_tag,
        account_job_parameters,
    )

    schedules = transform_schedules(get_schedules(api_session, base_url, timeout))
    logger.debug("Loading %d Opsgenie schedules", len(schedules))
    _load_and_cleanup(
        neo4j_session,
        OpsgenieScheduleSchema(),
        schedules,
        update_tag,
        account_job_parameters,
    )
    logger.info("Completed Opsgenie sync")
