import logging
from dataclasses import dataclass
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.intel.sentinelone.api import call_sentinelone_api
from cartography.intel.sentinelone.api import is_site_scope_http_error
from cartography.models.sentinelone.account import S1AccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SentinelOneSyncScope:
    account_id: str
    site_id: str | None = None


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
        passthrough_exceptions=is_site_scope_http_error,
    )

    accounts_data = response["data"]

    # Filter accounts by ID if specified
    if account_ids:
        accounts_data = [
            account for account in accounts_data if account["id"] in account_ids
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


@timeit
def get_sites(
    api_url: str,
    api_token: str,
    site_ids: list[str] | None = None,
    account_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Get site data for site-scoped SentinelOne users or targeted MSSP syncs.
    """
    logger.info("Retrieving SentinelOne site data")

    sites_data: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        params: dict[str, Any] = {"limit": 1000}
        if cursor:
            params["cursor"] = cursor

        response = call_sentinelone_api(
            api_url=api_url,
            endpoint="web/api/v2.1/sites",
            api_token=api_token,
            params=params,
        )

        page_sites = response["data"]["sites"]
        if not page_sites:
            break

        sites_data.extend(page_sites)
        cursor = (response.get("pagination") or {}).get("nextCursor")
        if not cursor:
            break

    if site_ids:
        allowed_site_ids = set(site_ids)
        sites_data = [site for site in sites_data if site["id"] in allowed_site_ids]
        logger.info(
            "Filtered SentinelOne sites to %d requested site IDs", len(sites_data)
        )
    if account_ids:
        allowed_account_ids = set(account_ids)
        sites_data = [
            site for site in sites_data if site["accountId"] in allowed_account_ids
        ]
        logger.info(
            "Filtered SentinelOne sites to %d matching parent accounts",
            len(sites_data),
        )

    if sites_data:
        logger.debug("Retrieved SentinelOne site data: %d sites", len(sites_data))
    else:
        logger.warning("No SentinelOne sites retrieved")

    return sites_data


def transform_accounts_from_sites(
    sites_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Synthesize account nodes from site metadata when account enumeration is forbidden.
    """
    accounts_by_id: dict[str, dict[str, Any]] = {}

    for site in sites_data:
        account_id = site["accountId"]
        active_licenses = site.get("activeLicenses")
        account = accounts_by_id.setdefault(
            account_id,
            {
                "id": account_id,
                "name": site.get("accountName"),
                "account_type": None,
                "active_agents": 0 if active_licenses is not None else None,
                # SentinelOne site records expose activeLicenses, not activeAgents.
                "created_at": site.get("createdAt"),
                "expiration": site.get("expiration"),
                "number_of_sites": 0,
                "state": site.get("state"),
            },
        )

        account["number_of_sites"] = (account.get("number_of_sites") or 0) + 1
        if active_licenses is not None:
            account["active_agents"] = (
                account.get("active_agents") or 0
            ) + active_licenses
        if account.get("name") is None:
            account["name"] = site.get("accountName")
        if account.get("created_at") is None:
            account["created_at"] = site.get("createdAt")
        if account.get("expiration") is None:
            account["expiration"] = site.get("expiration")
        if account.get("state") is None:
            account["state"] = site.get("state")

    return list(accounts_by_id.values())


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
    return synced_account_ids


@timeit
def sync_site_scoped_accounts(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    site_ids: list[str] | None = None,
    account_ids: list[str] | None = None,
) -> list[SentinelOneSyncScope]:
    """
    Sync SentinelOne sites when the token cannot enumerate accounts directly.
    """
    sites_raw_data = get_sites(
        common_job_parameters["API_URL"],
        common_job_parameters["API_TOKEN"],
        site_ids=site_ids,
        account_ids=account_ids,
    )

    transformed_accounts = transform_accounts_from_sites(sites_raw_data)
    load_accounts(
        neo4j_session,
        transformed_accounts,
        common_job_parameters["UPDATE_TAG"],
    )

    scopes = [
        SentinelOneSyncScope(account_id=site["accountId"], site_id=site["id"])
        for site in sites_raw_data
    ]
    logger.info(
        "Resolved %d SentinelOne site scopes across %d parent accounts",
        len(scopes),
        len(transformed_accounts),
    )
    return scopes
