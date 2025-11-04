import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

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
    common_job_parameters: Dict[str, Any],
) -> None:
    channels = get(slack_client, team_id, common_job_parameters['CHANNELS_MEMBERSHIPS'])
    load_channels(neo4j_session, channels, team_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(slack_client: WebClient, team_id: str, get_memberships: bool) -> List[Dict[str, Any]]:
    channels: List[Dict[str, Any]] = []
    for channel in slack_paginate(
        slack_client,
        'conversations_list',
        'channels',
        team_id=team_id,
    ):
        if channel['is_archived']:
            channels.append(channel)
        elif get_memberships:
            for member in slack_paginate(
                slack_client,
                'conversations_members',
                'members',
                channel=channel['id'],
            ):
                channel_m = channel.copy()
                channel_m['member_id'] = member
                channels.append(channel_m)
        else:
            channels.append(channel)
    return channels


def _get_membership(slack_client: WebClient, slack_channel: str, cursor: Optional[str] = None) -> List[str]:
    result = []
    memberships = slack_client.conversations_members(channel=slack_channel, cursor=cursor)
    for m in memberships['members']:
        result.append(m)
    next_cursor = memberships.get('response_metadata', {}).get('next_cursor', '')
    if next_cursor != '':
        result.extend(_get_membership(slack_client, slack_channel, cursor=next_cursor))
    return result


@timeit
def load_channels(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
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
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(SlackChannelSchema(), common_job_parameters).run(neo4j_session)
