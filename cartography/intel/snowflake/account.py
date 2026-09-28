import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.account import SnowflakeAccountSchema
from cartography.models.snowflake.account import SnowflakeManagedAccountSchema
from cartography.models.snowflake.account import SnowflakeOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_organization_accounts(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """List every account in the organization, or None when not permitted.

    ``GET /api/v2/accounts`` requires ORGADMIN, which most collector identities do
    not hold. A 403 or 404 is the normal case rather than an error, and the caller
    falls back to describing only the connected account.
    """
    try:
        return client.list_all("/api/v2/accounts")
    except requests.HTTPError as error:
        skip_or_raise_http(error, 401, 403, 404)
        logger.info(
            "Snowflake account %s cannot list organization accounts (ORGADMIN is "
            "not enabled for this role) - syncing the connected account only.",
            client.account_id,
        )
        return None


@timeit
def get_managed_accounts(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """List reader accounts, or None when the account has none or cannot list them."""
    try:
        return client.list_all("/api/v2/managed-accounts")
    except requests.HTTPError as error:
        skip_or_raise_http(error, 401, 403, 404)
        return None


def transform_accounts(
    accounts: list[dict[str, Any]] | None,
    account_id: str,
) -> list[dict[str, Any]]:
    """Shape the organization's accounts, guaranteeing the connected one is present.

    Sibling accounts are recorded so that share and replication targets resolve to
    a real node, but only the connected account gets its objects synced, which
    ``is_current`` records. When the listing was unavailable the connected account
    is still emitted from its identifier alone, so the tenant node always exists.
    """
    organization_name, _, name = account_id.partition(".")
    transformed: list[dict[str, Any]] = []
    seen_current = False

    for account in accounts or []:
        account_organization = account.get("organization_name") or organization_name
        account_name = account["name"]
        node_id = f"{account_organization}.{account_name}".upper()
        is_current = node_id == account_id
        seen_current = seen_current or is_current
        transformed.append(
            {
                "id": node_id,
                "name": account_name,
                "organization_name": account_organization,
                "edition": account.get("edition"),
                "region": account.get("region"),
                "region_group": account.get("region_group"),
                "account_url": account.get("account_url"),
                "account_locator": account.get("account_locator"),
                "is_org_admin": account.get("is_org_admin"),
                "retention_time": account.get("retention_time"),
                "comment": account.get("comment"),
                "created_on": iso_to_datetime(account.get("created_on")),
                "dropped_on": iso_to_datetime(account.get("dropped_on")),
                "scheduled_deletion_time": iso_to_datetime(
                    account.get("scheduled_deletion_time"),
                ),
                "is_current": is_current,
            },
        )

    if not seen_current:
        transformed.append(
            {
                "id": account_id,
                "name": name,
                "organization_name": organization_name,
                "edition": None,
                "region": None,
                "region_group": None,
                "account_url": None,
                "account_locator": None,
                "is_org_admin": None,
                "retention_time": None,
                "comment": None,
                "created_on": None,
                "dropped_on": None,
                "scheduled_deletion_time": None,
                "is_current": True,
            },
        )
    return transformed


def transform_managed_accounts(
    managed_accounts: list[dict[str, Any]] | None,
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for managed_account in managed_accounts or []:
        name = managed_account["name"]
        account_type = managed_account.get("account_type")
        transformed.append(
            {
                "id": sf_id(account_id, "managed_account", name),
                "name": name,
                "account_type": account_type,
                "is_reader": account_type == "READER",
                "locator": managed_account.get("account_locator")
                or managed_account.get("locator"),
                "url": managed_account.get("account_locator_url")
                or managed_account.get("url"),
                "cloud": managed_account.get("cloud"),
                "region": managed_account.get("region"),
                "comment": managed_account.get("comment"),
                "created_on": iso_to_datetime(managed_account.get("created_on")),
            },
        )
    return transformed


def load_accounts(
    neo4j_session: neo4j.Session,
    accounts: list[dict[str, Any]],
    update_tag: int,
) -> None:
    organizations = sorted(
        {
            account["organization_name"]
            for account in accounts
            if account["organization_name"]
        },
    )
    load(
        neo4j_session,
        SnowflakeOrganizationSchema(),
        [{"id": name, "name": name} for name in organizations],
        lastupdated=update_tag,
    )
    load(
        neo4j_session,
        SnowflakeAccountSchema(),
        accounts,
        lastupdated=update_tag,
    )


def load_managed_accounts(
    neo4j_session: neo4j.Session,
    managed_accounts: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeManagedAccountSchema(),
        managed_accounts,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeManagedAccountSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync the account tenant node, its organization, and its managed accounts.

    Runs first: every other node's RESOURCE edge matches the account node, so it
    has to exist before anything else loads.

    Returns whether the managed-account listing was readable. It is the only part of
    this sync that gets a cleanup job (the account and organization nodes are
    unscoped and never deleted), and an unreadable listing is indistinguishable from
    an empty one once it has been transformed, so the caller must be told not to run
    that cleanup. Otherwise a role that loses ``MANAGE ACCOUNTS`` silently erases
    every reader account previously ingested.
    """
    accounts = transform_accounts(get_organization_accounts(client), client.account_id)
    load_accounts(neo4j_session, accounts, common_job_parameters["UPDATE_TAG"])

    raw_managed_accounts = get_managed_accounts(client)
    if raw_managed_accounts is None:
        logger.warning(
            "Snowflake managed accounts could not be listed for account %s; leaving "
            "any previously ingested reader accounts in place.",
            client.account_id,
        )
        return False

    managed_accounts = transform_managed_accounts(
        raw_managed_accounts, client.account_id
    )
    load_managed_accounts(
        neo4j_session,
        managed_accounts,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
