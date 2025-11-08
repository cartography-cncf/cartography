import logging
from typing import Any

import neo4j
from slack_sdk import WebClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.slack.utils import slack_paginate
from cartography.models.slack.channels import SlackChannelSchema
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
    channels = get(slack_client, team_id, common_job_parameters["CHANNELS_MEMBERSHIPS"])
    load_channels(neo4j_session, channels, team_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    slack_client: WebClient, team_id: str, get_memberships: bool
) -> list[dict[str, Any]]:
    channels: list[dict[str, Any]] = []
    for channel in slack_paginate(
        slack_client,
        "conversations_list",
        "channels",
        team_id=team_id,
    ):
        if channel["is_archived"]:
            channels.append(channel)
        elif get_memberships:
            for member in slack_paginate(
                slack_client,
                "conversations_members",
                "members",
                channel=channel["id"],
            ):
                channel_m = channel.copy()
                channel_m["member_id"] = member
                channels.append(channel_m)
        else:
            channels.append(channel)
    return channels


@timeit
def load_channels(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %s Slack channels into Neo4j", len(data))
    load(
        neo4j_session,
        SlackChannelSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SlackChannelSchema(), common_job_parameters).run(
        neo4j_session
    )
