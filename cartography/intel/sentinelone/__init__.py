import logging
from collections import defaultdict

import neo4j
import requests

import cartography.intel.sentinelone.agent
import cartography.intel.sentinelone.application
import cartography.intel.sentinelone.finding
from cartography.config import Config
from cartography.intel.sentinelone.account import SentinelOneSyncScope
from cartography.intel.sentinelone.account import sync_accounts
from cartography.intel.sentinelone.account import sync_site_scoped_accounts
from cartography.intel.sentinelone.api import is_site_scope_http_error
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _sync_scope(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, object],
    account_id: str,
    site_ids: list[str] | None = None,
    *,
    do_cleanup: bool = True,
) -> None:
    common_job_parameters["S1_ACCOUNT_ID"] = account_id

    if not site_ids:
        common_job_parameters.pop("S1_SITE_ID", None)
        cartography.intel.sentinelone.agent.sync(
            neo4j_session,
            common_job_parameters,
        )
        cartography.intel.sentinelone.application.sync(
            neo4j_session,
            common_job_parameters,
        )
        cartography.intel.sentinelone.finding.sync(
            neo4j_session,
            common_job_parameters,
        )
        common_job_parameters.pop("S1_ACCOUNT_ID", None)
        return

    for site_id in site_ids:
        common_job_parameters["S1_SITE_ID"] = site_id
        cartography.intel.sentinelone.agent.sync(
            neo4j_session,
            common_job_parameters,
            do_cleanup=False,
        )
        cartography.intel.sentinelone.application.sync(
            neo4j_session,
            common_job_parameters,
            do_cleanup=False,
        )
        cartography.intel.sentinelone.finding.sync(
            neo4j_session,
            common_job_parameters,
            do_cleanup=False,
        )

    if not do_cleanup:
        common_job_parameters.pop("S1_SITE_ID", None)
        common_job_parameters.pop("S1_ACCOUNT_ID", None)
        return

    common_job_parameters.pop("S1_SITE_ID", None)
    cartography.intel.sentinelone.agent.cleanup(neo4j_session, common_job_parameters)
    cartography.intel.sentinelone.application.cleanup(
        neo4j_session,
        common_job_parameters,
    )
    cartography.intel.sentinelone.finding.cleanup(
        neo4j_session,
        common_job_parameters,
    )
    common_job_parameters.pop("S1_ACCOUNT_ID", None)


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

    if config.sentinelone_site_ids:
        logger.info(
            "Syncing SentinelOne using explicit site scope for %d sites",
            len(config.sentinelone_site_ids),
        )
        logger.warning(
            "Skipping SentinelOne cleanup for explicit site-scoped syncs to avoid deleting data from sibling sites under the same account",
        )
        scopes = sync_site_scoped_accounts(
            neo4j_session,
            common_job_parameters,
            site_ids=config.sentinelone_site_ids,
            account_ids=config.sentinelone_account_ids,
        )
    else:
        try:
            synced_account_ids = sync_accounts(
                neo4j_session,
                common_job_parameters,
                config.sentinelone_account_ids,
            )
            scopes = [
                SentinelOneSyncScope(account_id=account_id)
                for account_id in synced_account_ids
            ]
        except requests.exceptions.HTTPError as exc:
            if not is_site_scope_http_error(exc):
                raise
            logger.warning(
                "SentinelOne token cannot enumerate /accounts for a site-scoped user; continuing with site-scoped sync fallback",
            )
            scopes = sync_site_scoped_accounts(
                neo4j_session,
                common_job_parameters,
                account_ids=config.sentinelone_account_ids,
            )

    site_ids_by_account: dict[str, list[str]] = defaultdict(list)
    for scope in scopes:
        if scope.site_id:
            site_ids_by_account[scope.account_id].append(scope.site_id)
        else:
            site_ids_by_account.setdefault(scope.account_id, [])

    for account_id, site_ids in site_ids_by_account.items():
        _sync_scope(
            neo4j_session,
            common_job_parameters,
            account_id,
            site_ids=site_ids or None,
            do_cleanup=not bool(config.sentinelone_site_ids),
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
