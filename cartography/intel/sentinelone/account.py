import logging
import re
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


def _camel_to_snake(name: str) -> str:
    """
    Convert a camelCase string to snake_case
    :param name: The camelCase string
    :return: The snake_case string
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


@timeit
def fetch_accounts(api_url: str, api_token: str, account_ids: list[str] | None = None) -> list[S1Account]:
    """
    Get account data from SentinelOne API
    :param api_url: The SentinelOne API URL
    :param api_token: The SentinelOne API token
    :param account_ids: Optional list of account IDs to filter for
    :return: Account data
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

    # Transform camelCase keys to snake_case
    transformed_accounts_data: list[S1Account] = []
    for account in accounts_data:
        snake_case_account = {_camel_to_snake(key): value for key, value in account.items()}
        transformed_account: S1Account = {
            'id': snake_case_account.get('id', ''),
            'account_type': snake_case_account.get('account_type', ''),
            'active_agents': snake_case_account.get('active_agents'),
            'created_at': snake_case_account.get('created_at', ''),
            'expiration': snake_case_account.get('expiration', ''),
            'name': snake_case_account.get('name', ''),
            'number_of_sites': snake_case_account.get('number_of_sites'),
            'state': snake_case_account.get('state', ''),
        }
        transformed_accounts_data.append(transformed_account)

    if transformed_accounts_data:
        logger.info(f"Retrieved SentinelOne account data: {len(transformed_accounts_data)} accounts")
    else:
        logger.warning("No SentinelOne accounts retrieved")

    return transformed_accounts_data


@timeit
def ensure_account_node(
    neo4j_session: neo4j.Session,
    account_data: S1Account,
    update_tag: int,
) -> None:
    query = """
    MERGE (account:S1Account {id: $id})
    ON CREATE SET account.firstseen = timestamp()
    SET account.name = $name,
        account.account_type = $account_type,
        account.active_agents = $active_agents,
        account.created_at = $created_at,
        account.expiration = $expiration,
        account.number_of_sites = $number_of_sites,
        account.state = $state,
        account.lastupdated = $update_tag
    """
    neo4j_session.run(
        query,
        update_tag=update_tag,
        **account_data,
    )

    logger.info(f"Created or updated SentinelOne account node with ID: {account_data.get('id')}")


@timeit
def sync_account(
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
    s1_accounts = fetch_accounts(api_url, api_token, account_ids)
    synced_account_ids = []
    for account in s1_accounts:
        account_id = account.get('id')
        if not account_id:
            logger.warning("Encountered account without ID, skipping")
            continue

        ensure_account_node(neo4j_session, account, update_tag)
        synced_account_ids.append(account_id)

    if not synced_account_ids:
        logger.warning("No accounts were synced from SentinelOne API")
    else:
        logger.info(f"Synced {len(synced_account_ids)} SentinelOne accounts")

    return synced_account_ids
