import logging

import neo4j

import cartography.intel.sentinelone.agent
import cartography.intel.sentinelone.application
import cartography.intel.sentinelone.cve
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

    # Set up common job parameters
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "API_URL": config.sentinelone_api_url,
        "API_TOKEN": config.sentinelone_api_token,
    }

    # Sync SentinelOne account data (needs to be done first to establish the account nodes)
    synced_account_ids = sync_accounts(
        neo4j_session,
        common_job_parameters,
        config.sentinelone_account_ids,
    )

    # Sync agents and applications for each account
    for account_id in synced_account_ids:
        # Add account-specific parameter
        common_job_parameters["S1_ACCOUNT_ID"] = account_id

        cartography.intel.sentinelone.agent.sync(
            neo4j_session,
            common_job_parameters,
        )

        cartography.intel.sentinelone.application.sync(
            neo4j_session,
            common_job_parameters,
        )

        cartography.intel.sentinelone.cve.sync(
            neo4j_session,
            common_job_parameters,
        )

        # Clean up account-specific parameters
        del common_job_parameters["S1_ACCOUNT_ID"]

    # Record that the sync is complete
    merge_module_sync_metadata(
        neo4j_session,
        group_type="SentinelOne",
        group_id="sentinelone",
        synced_type="SentinelOneData",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
