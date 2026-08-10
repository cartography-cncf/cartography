import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.account import NetlifyAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_account(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_slug: str,
    update_tag: int,
) -> dict[str, Any]:
    """
    Load the Netlify team that every other resource hangs off, and return its raw payload.

    There is no cleanup job here: the tenant node is the anchor for every scoped cleanup in the
    module, so deleting it would have to happen after all its children, and a single-team sync
    has no way to tell a team that was removed from a team the token merely lost access to.

    :return: The raw account payload, whose `id` scopes the rest of the sync.
    """
    accounts = get_netlify_accounts(api_session, base_url)
    account = _select_account(accounts, account_slug)
    load_netlify_accounts(neo4j_session, [account], update_tag)
    return account


@timeit
def get_netlify_accounts(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return paginated_get(api_session, f"{base_url}/accounts")


def _select_account(
    accounts: list[dict[str, Any]],
    account_slug: str,
) -> dict[str, Any]:
    """
    Pick the requested team out of every team the token can see.

    Fails loudly rather than syncing nothing: an unrecognised slug is a configuration error,
    and silently returning no account would let every cleanup job wipe the previous run's data.
    """
    for account in accounts:
        if account["slug"] == account_slug:
            return account
    visible = ", ".join(sorted(a["slug"] for a in accounts)) or "none"
    raise ValueError(
        f"Netlify account slug '{account_slug}' was not found. "
        f"Slugs visible to this token: {visible}.",
    )


@timeit
def load_netlify_accounts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyAccountSchema(),
        data,
        lastupdated=update_tag,
    )
