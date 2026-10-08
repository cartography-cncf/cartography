import logging
from datetime import datetime
from datetime import timezone
from typing import Any

import neo4j
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.slack.utils import slack_paginate
from cartography.models.slack.bot import SlackBotSchema
from cartography.models.slack.user import SlackUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# team.accessLogs needs a user token with the `admin` scope on a paid workspace.
# These errors mean the token or plan cannot read access logs, so we skip
# last-login enrichment instead of failing the sync.
_ACCESS_LOGS_UNAVAILABLE_ERRORS = {
    "access_denied",
    "missing_scope",
    "no_permission",
    "not_allowed_token_type",
    "paid_only",
}
# Slack asks for a cursor-pagination limit below 1000.
_ACCESS_LOGS_PAGE_SIZE = 999


@timeit
def sync(
    neo4j_session: neo4j.Session,
    slack_client: WebClient,
    team_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    members = get(slack_client, team_id)
    last_logins = get_last_logins(slack_client, team_id)
    users, bots = transform(members, last_logins)
    load_users(neo4j_session, users, team_id, update_tag)
    load_bots(neo4j_session, bots, team_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(slack_client: WebClient, team_id: str) -> list[dict[str, Any]]:
    return slack_paginate(slack_client, "users_list", "members", team_id=team_id)


@timeit
def get_last_logins(slack_client: WebClient, team_id: str) -> dict[str, int]:
    """
    Return the most recent access-log timestamp for each user ID.

    Slack reports one access-log entry per user, IP address and user agent, so a
    user's last login is the latest `date_last` across their entries. Returns an
    empty dict when the token or workspace plan cannot read access logs.
    """
    try:
        logins = slack_paginate(
            slack_client,
            "team_accessLogs",
            "logins",
            team_id=team_id,
            limit=_ACCESS_LOGS_PAGE_SIZE,
        )
    except SlackApiError as error:
        error_code = error.response.get("error")
        if error_code not in _ACCESS_LOGS_UNAVAILABLE_ERRORS:
            raise
        logger.warning(
            "Slack token cannot read access logs for team %s (%s); skipping user "
            "last-login enrichment. This requires a user token with the `admin` "
            "scope on a paid workspace.",
            team_id,
            error_code,
        )
        return {}

    last_logins: dict[str, int] = {}
    for login in logins:
        user_id = login.get("user_id")
        date_last = login.get("date_last")
        if not user_id or date_last is None:
            continue
        last_logins[user_id] = max(last_logins.get(user_id, 0), int(date_last))
    return last_logins


def transform(
    members: list[dict[str, Any]],
    last_logins: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split Slack members into human users and bots."""
    users = []
    bots = []
    for member in members:
        # is_bot: traditional bot integrations; is_app_user: newer Slack-app-created accounts.
        # Both are non-human and should be ingested as SlackBot, not SlackUser.
        if member.get("is_bot") or member.get("is_app_user"):
            bots.append(member)
        else:
            last_login = last_logins.get(member["id"])
            users.append(
                {
                    **member,
                    "last_login": (
                        datetime.fromtimestamp(last_login, tz=timezone.utc)
                        if last_login is not None
                        else None
                    ),
                },
            )
    return users, bots


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SlackUserSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


@timeit
def load_bots(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SlackBotSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SlackUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(SlackBotSchema(), common_job_parameters).run(
        neo4j_session,
    )
