import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.intel.sentinelone.api import call_sentinelone_api
from cartography.models.sentinelone.account import S1AccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_accounts(
    api_url: str, api_token: str, account_ids: list[str] | None = None
) -> list[dict[str, Any]]:
    """
    Get account data from SentinelOne API
    :param api_url: The SentinelOne API URL
    :param api_token: The SentinelOne API token
    :param account_ids: Optional list of account IDs to filter for
    :return: Raw account data from API
    """
    logger.info("Retrieving SentinelOne account data")

    # Get accounts info
    response = call_sentinelone_api(
        api_url=api_url,
        endpoint="web/api/v2.1/accounts",
        api_token=api_token,
    )

    accounts_data = response.get("data", [])

    # Filter accounts by ID if specified
    if account_ids:
        accounts_data = [
            account for account in accounts_data if account.get("id") in account_ids
        ]
        logger.info(f"Filtered accounts data to {len(accounts_data)} matching accounts")

    if accounts_data:
        logger.info(
            f"Retrieved SentinelOne account data: {len(accounts_data)} accounts"
        )
    else:
        logger.warning("No SentinelOne accounts retrieved")

    return accounts_data


def transform_accounts(accounts_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform raw account data into standardized format for Neo4j ingestion
    :param accounts_data: Raw account data from API
    :return: List of transformed account data
    """
    result: list[dict[str, Any]] = []

    for account in accounts_data:
        transformed_account = {
            # Required fields - use direct access (will raise KeyError if missing)
            "id": account["id"],
            # Optional fields - use .get() with None default
            "name": account.get("name"),
            "account_type": account.get("accountType"),
            "active_agents": account.get("activeAgents"),
            "created_at": account.get("createdAt"),
            "expiration": account.get("expiration"),
            "number_of_sites": account.get("numberOfSites"),
            "state": account.get("state"),
        }
        result.append(transformed_account)

    return result


def load_accounts(
    neo4j_session: neo4j.Session,
    accounts_data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load SentinelOne account data into Neo4j using the data model
    :param neo4j_session: Neo4j session
    :param accounts_data: List of account data to load
    :param update_tag: Update tag for tracking data freshness
    """
    if not accounts_data:
        logger.warning("No account data provided to load_accounts")
        return

    load(
        neo4j_session,
        S1AccountSchema(),
        accounts_data,
        lastupdated=update_tag,
        firstseen=update_tag,
    )

    logger.info(f"Loaded {len(accounts_data)} SentinelOne account nodes")


@timeit
def sync_accounts(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    account_ids: list[str] | None = None,
) -> list[str]:
    """
    Sync SentinelOne account data using the modern sync pattern
    :param neo4j_session: Neo4j session
    :param api_url: SentinelOne API URL
    :param api_token: SentinelOne API token
    :param update_tag: Update tag for tracking data freshness
    :param common_job_parameters: Job parameters for cleanup
    :param account_ids: Optional list of account IDs to filter for
    :return: List of synced account IDs
    """
    # 1. GET - Fetch data from API
    accounts_raw_data = get_accounts(
        common_job_parameters["API_URL"],
        common_job_parameters["API_TOKEN"],
        account_ids,
    )

    # 2. TRANSFORM - Shape data for ingestion
    transformed_accounts = transform_accounts(accounts_raw_data)

    # 3. LOAD - Ingest to Neo4j using data model
    load_accounts(
        neo4j_session,
        transformed_accounts,
        common_job_parameters["UPDATE_TAG"],
    )

    synced_account_ids = [account["id"] for account in transformed_accounts]
    logger.info(f"Synced {len(synced_account_ids)} SentinelOne accounts")
    return synced_account_ids
