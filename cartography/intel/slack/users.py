from typing import Any

import neo4j
from slack_sdk import WebClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.slack.utils import slack_paginate
from cartography.models.slack.bot import SlackBotSchema
from cartography.models.slack.user import SlackUserSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    slack_client: WebClient,
    team_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    members = get(slack_client, team_id)
    users, bots = transform(members)
    load_users(neo4j_session, users, team_id, update_tag)
    load_bots(neo4j_session, bots, team_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(slack_client: WebClient, team_id: str) -> list[dict[str, Any]]:
    return slack_paginate(slack_client, "users_list", "members", team_id=team_id)


def transform(
    members: list[dict[str, Any]],
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
            users.append(member)
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
