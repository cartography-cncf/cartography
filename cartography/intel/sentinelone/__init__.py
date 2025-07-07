import logging

import neo4j

from cartography.config import Config
from cartography.intel.sentinelone.account import sync_accounts
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_sentinelone_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Perform ingestion of SentinelOne data.
    :param neo4j_session: Neo4j session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.sentinelone_api_token or not config.sentinelone_api_url:
        logger.info("SentinelOne API configuration not found - skipping this module.")
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Sync SentinelOne account data (needs to be done first to establish the account node)
    sync_accounts(
        neo4j_session,
        config.sentinelone_api_url,
        config.sentinelone_api_token,
        config.update_tag,
        common_job_parameters,
    )

    # Record that the sync is complete
    merge_module_sync_metadata(
        neo4j_session,
        group_type="SentinelOne",
        group_id="sentinelone",
        synced_type="SentinelOneData",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
