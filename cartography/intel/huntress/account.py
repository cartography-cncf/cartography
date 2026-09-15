import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.huntress.util import get_huntress_item
from cartography.intel.huntress.util import required_id
from cartography.models.huntress.account import HuntressAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(api_session: requests.Session, base_uri: str) -> dict[str, Any]:
    return get_huntress_item(api_session, base_uri, "account", "account")


def transform(api_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": required_id(api_result, "Account"),
        "name": api_result.get("name"),
        "subdomain": api_result.get("subdomain"),
        "status": api_result.get("status"),
        "support_type": api_result.get("support_type"),
    }


def load_account(
    neo4j_session: neo4j.Session,
    data: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        HuntressAccountSchema(),
        [data],
        lastupdated=update_tag,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_uri: str,
    update_tag: int,
) -> int:
    """Load the account node and return its ID, which scopes every other Huntress sync.

    The account is the tenant, so it has no cleanup job of its own: the credentials only
    ever resolve to one account, and deleting it would detach everything hanging off it.
    """
    raw_data = get(api_session, base_uri)
    account = transform(raw_data)
    load_account(neo4j_session, account, update_tag)
    return account["id"]
