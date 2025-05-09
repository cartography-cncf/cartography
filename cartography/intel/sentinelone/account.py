import logging
from typing import TypedDict

import neo4j

from cartography.intel.sentinelone.utils import call_sentinelone_api
from cartography.util import timeit

logger = logging.getLogger(__name__)


class S1Account(TypedDict):
    id: str
    account_type: str
    active_agents: int | None
    created_at: str
    expiration: str
    name: str
    number_of_sites: int | None
    state: str


def _transform_accounts(accounts_data: list[dict]) -> list[S1Account]:
    """
    Transform raw account data into standardized S1Account format
    :param accounts_data: Raw account data from API
    :return: List of transformed S1Account objects
    """
    transformed_accounts_data: list[S1Account] = []
    for account in accounts_data:
        transformed_account: S1Account = {
            'id': account.get('id', ''),
            'account_type': account.get('accountType', ''),
            'active_agents': account.get('activeAgents'),
            'created_at': account.get('createdAt', ''),
            'expiration': account.get('expiration', ''),
            'name': account.get('name', ''),
            'number_of_sites': account.get('numberOfSites'),
            'state': account.get('state', ''),
        }
        transformed_accounts_data.append(transformed_account)

    return transformed_accounts_data


@timeit
def _fetch_accounts(api_url: str, api_token: str, account_ids: list[str] | None = None) -> list[dict]:
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

    accounts_data = response.get('data', [])

    # Filter accounts by ID if specified
    if account_ids:
        accounts_data = [account for account in accounts_data if account.get('id') in account_ids]
        logger.info(f"Filtered accounts data to {len(accounts_data)} matching accounts")

    if accounts_data:
        logger.info(f"Retrieved SentinelOne account data: {len(accounts_data)} accounts")
    else:
        logger.warning("No SentinelOne accounts retrieved")

    return accounts_data


@timeit
def load_accounts(
    neo4j_session: neo4j.Session,
    accounts_data: list[S1Account],
    update_tag: int,
) -> None:
    """
    Create or update S1Account nodes in Neo4j for multiple accounts
    :param neo4j_session: Neo4j session
    :param accounts_data: List of account data to process
    :param update_tag: Update tag
    """
    if not accounts_data:
        logger.warning("No account data provided to ensure_account_nodes")
        return

    query = """
    UNWIND $accounts as account
    MERGE (a:S1Account {id: account.id})
    ON CREATE SET a.firstseen = timestamp()
    SET a.name = account.name,
        a.account_type = account.account_type,
        a.active_agents = account.active_agents,
        a.created_at = account.created_at,
        a.expiration = account.expiration,
        a.number_of_sites = account.number_of_sites,
        a.state = account.state,
        a.lastupdated = $update_tag
    """
    neo4j_session.run(
        query,
        accounts=accounts_data,
        update_tag=update_tag,
    )

    logger.info(f"Created or updated {len(accounts_data)} SentinelOne account nodes")


@timeit
def sync_accounts(
    neo4j_session: neo4j.Session,
    api_url: str,
    api_token: str,
    update_tag: int,
    account_ids: list[str] | None = None,
) -> list[str]:
    """
    Sync SentinelOne account data
    :param neo4j_session: Neo4j session
    :param api_url: SentinelOne API URL
    :param api_token: SentinelOne API token
    :param update_tag: Update tag
    :param account_ids: Optional list of account IDs to filter for
    :return: List of synced account IDs
    """
    accounts_raw_data = _fetch_accounts(api_url, api_token, account_ids)
    s1_accounts = _transform_accounts(accounts_raw_data)
    load_accounts(neo4j_session, s1_accounts, update_tag)
    synced_account_ids = [account['id'] for account in s1_accounts]
    logger.info(f"Synced {len(synced_account_ids)} SentinelOne accounts")
    return synced_account_ids
