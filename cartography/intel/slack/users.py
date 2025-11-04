import logging
from typing import Any

import neo4j
from slack_sdk import WebClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.slack.utils import slack_paginate
from cartography.models.slack.user import SlackUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    slack_client: WebClient,
    team_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    users = get(slack_client, team_id)
    load_users(neo4j_session, users, team_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(slack_client: WebClient, team_id: str) -> list[dict[str, Any]]:
    return slack_paginate(slack_client, "users_list", "members", team_id=team_id)


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %s Slack users into Neo4j", len(data))
    load(
        neo4j_session,
        SlackUserSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SlackUserSchema(), common_job_parameters).run(
        neo4j_session
    )
