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


def transform_users(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        schema,
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    GraphJob.from_node_schema(
        schema,
        {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id},
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    timeout: int,
    update_tag: int,
) -> None:
    account = transform_account(get_account(api_session, base_url, timeout))
    account_id = account[0]["id"]
    logger.info("Loading Opsgenie account")
    load(
        neo4j_session,
        OpsgenieAccountSchema(),
        account,
        lastupdated=update_tag,
    )

    teams = transform_teams(get_teams(api_session, base_url, timeout))
    logger.info("Loading %d Opsgenie teams", len(teams))
    _load_and_cleanup(
        neo4j_session,
        OpsgenieTeamSchema(),
        teams,
        account_id,
        update_tag,
    )

    users = transform_users(get_users(api_session, base_url, timeout))
    logger.info("Loading %d Opsgenie users", len(users))
    _load_and_cleanup(
        neo4j_session,
        OpsgenieUserSchema(),
        users,
        account_id,
        update_tag,
    )

    schedules = transform_schedules(get_schedules(api_session, base_url, timeout))
    logger.info("Loading %d Opsgenie schedules", len(schedules))
    _load_and_cleanup(
        neo4j_session,
        OpsgenieScheduleSchema(),
        schedules,
        account_id,
        update_tag,
    )
