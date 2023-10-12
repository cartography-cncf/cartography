import logging

import neo4j
from slack_sdk import WebClient
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

import cartography.intel.slack.channels
import cartography.intel.slack.groups
import cartography.intel.slack.team
import cartography.intel.slack.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_slack_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Slack data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if not config.slack_token or not config.slack_teams:
        logger.info(
            'Slack import is not configured - skipping this module. '
            'See docs to configure.',
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "CHANNELS_MEMBERSHIPS": config.slack_channels_memberships,
    }

    rate_limit_handler = RateLimitErrorRetryHandler(max_retry_count=1)
    slack_client = WebClient(token=config.slack_token)
    slack_client.retry_handlers.append(rate_limit_handler)

    for team_id in config.slack_teams.split(','):
        logger.info("Syncing team %s", team_id)
        common_job_parameters['TEAM_ID'] = team_id
        cartography.intel.slack.team.sync(
            neo4j_session,
            slack_client,
            team_id,
            config.update_tag,
            common_job_parameters,
        )
        cartography.intel.slack.users.sync(
            neo4j_session,
            slack_client,
            team_id,
            config.update_tag,
            common_job_parameters,
        )
        cartography.intel.slack.channels.sync(
            neo4j_session,
            slack_client,
            team_id,
            config.update_tag,
            common_job_parameters,
        )
        cartography.intel.slack.groups.sync(
            neo4j_session,
            slack_client,
            team_id,
            config.update_tag,
            common_job_parameters,
        )
