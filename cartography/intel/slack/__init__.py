import logging

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.util.lazy import lazy_callable

logger = logging.getLogger(__name__)

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
RateLimitErrorRetryHandler = lazy_callable(
    "slack_sdk.http_retry.builtin_handlers", "RateLimitErrorRetryHandler"
)
WebClient = lazy_callable("slack_sdk", "WebClient")
sync_channels = lazy_callable("cartography.intel.slack.channels", "sync")
sync_groups = lazy_callable("cartography.intel.slack.groups", "sync")
sync_teams = lazy_callable("cartography.intel.slack.teams", "sync")
sync_users = lazy_callable("cartography.intel.slack.users", "sync")


@timeit
def start_slack_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Slack data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.slack_token:
        logger.info(
            "Slack import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "CHANNELS_MEMBERSHIPS": config.slack_channels_memberships,
    }

    restricting_teams = []
    if config.slack_teams:
        for team in config.slack_teams.split(","):
            restricting_teams.append(team.strip())

    rate_limit_handler = RateLimitErrorRetryHandler(max_retry_count=1)
    slack_client = WebClient(token=config.slack_token)
    slack_client.retry_handlers.append(rate_limit_handler)

    teams_id = sync_teams(
        neo4j_session,
        slack_client,
        config.update_tag,
        common_job_parameters,
    )
    for team_id in teams_id:
        if restricting_teams and team_id not in restricting_teams:
            logger.debug("Skipping team %s", team_id)
            continue
        logger.info("Syncing team %s", team_id)
        common_job_parameters["TEAM_ID"] = team_id
        sync_users(
            neo4j_session,
            slack_client,
            team_id,
            config.update_tag,
            common_job_parameters,
        )
        sync_channels(
            neo4j_session,
            slack_client,
            team_id,
            config.update_tag,
            common_job_parameters,
        )
        sync_groups(
            neo4j_session,
            slack_client,
            team_id,
            config.update_tag,
            common_job_parameters,
        )
