"""Snowflake shares.

A share is the mechanism by which data leaves a Snowflake account without being
copied, so an outbound share plus its consumer list is a standing egress path.
Nothing about shares is exposed by the REST API: the listing comes from
``SHOW SHARES``, the exposed objects from ``SHOW GRANTS TO SHARE`` and the consumer
accounts from ``SHOW GRANTS OF SHARE``.

The two per-share statements are only issued for outbound shares. An inbound share
is owned by the producer account, so asking what it grants or who consumes it is not
a privilege gap on this side and must not be treated as one.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.grants import securable_id
from cartography.intel.snowflake.names import name_list
from cartography.intel.snowflake.names import share_key
from cartography.intel.snowflake.names import split_qualified_name
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.share import SnowflakeShareSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_OUTBOUND = "OUTBOUND"


@timeit
def get_shares(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every share visible to the account, or None when not permitted."""
    try:
        return client.run_sql("SHOW SHARES")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable("shares", "SHOW SHARES is not permitted")
        return None


@timeit
def get_share_grants(
    client: SnowflakeClient, share_name: str
) -> list[dict[str, Any]] | None:
    """Objects one share exposes, or None when the share is not readable."""
    try:
        return client.run_sql(f"SHOW GRANTS TO SHARE {sf_fqn(share_name)}")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            f"share {share_name} contents", "SHOW GRANTS TO SHARE is not permitted"
        )
        return None


@timeit
def get_share_consumers(
    client: SnowflakeClient, share_name: str
) -> list[dict[str, Any]] | None:
    """Consumer accounts of one share, or None when the share is not readable."""
    try:
        return client.run_sql(f"SHOW GRANTS OF SHARE {sf_fqn(share_name)}")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            f"share {share_name} consumers", "SHOW GRANTS OF SHARE is not permitted"
        )
        return None


def _split_object_name(name: str) -> dict[str, str | None]:
    """Split a share grant's dotted object name into its identifier components.

    ``SHOW GRANTS TO SHARE`` reports the target as one already-qualified string,
    whereas node ids are built from the components, so it has to be taken apart
    before the id can be recomputed.
    """
    parts = split_qualified_name(name)
    if len(parts) == 1:
        return {"name": parts[0]}
    if len(parts) == 2:
        return {"database": parts[0], "name": parts[1]}
    return {"database": parts[0], "schema": parts[1], "name": parts[2]}


def _consumer_account_id(account_id: str, consumer: str) -> str:
    """Resolve a consumer account reference to a managed account node id.

    Consumers are reported organization-qualified, while a managed account this
    account created is keyed on its bare name.
    """
    return sf_id(account_id, "managed_account", consumer.split(".")[-1])


def transform(
    shares: list[dict[str, Any]],
    grants_by_share: dict[str, list[dict[str, Any]]],
    consumers_by_share: dict[str, list[dict[str, Any]]],
    account_id: str,
) -> tuple[list[dict[str, Any]], int]:
    """Shape share rows, their exposed objects and their consumers into nodes.

    Returns the nodes plus the number of exposed objects skipped because Cartography
    does not model their object type.
    """
    transformed: list[dict[str, Any]] = []
    unmodelled = 0

    for share in shares:
        name = share["name"]
        owner_account = to_text(share.get("owner_account"))
        grants = grants_by_share.get(name, [])
        shared_object_ids: list[str] = []
        for grant in grants:
            object_name = to_text(grant.get("name"))
            if not object_name:
                continue
            object_id = securable_id(
                _split_object_name(object_name),
                to_text(grant.get("granted_on")),
                account_id,
            )
            if not object_id:
                unmodelled += 1
                continue
            shared_object_ids.append(object_id)

        consumers = {
            consumer
            for row in consumers_by_share.get(name, [])
            for consumer in [to_text(row.get("grantee_name"))]
            if consumer
        }
        consumers.update(name_list(share.get("to")))

        transformed.append(
            {
                "id": sf_id(account_id, "share", share_key(owner_account, name)),
                "name": name,
                "owner_account": owner_account,
                "share_kind": to_text(share.get("kind")),
                "database_name": to_text(share.get("database_name")),
                "owner": to_text(share.get("owner")),
                "comment": to_text(share.get("comment")),
                "created_on": iso_to_datetime(share.get("created_on")),
                "listing_global_name": to_text(share.get("listing_global_name")),
                "shared_with_accounts": sorted(consumers),
                "shared_with_account_count": len(consumers),
                "shared_with_account_ids": sorted(
                    _consumer_account_id(account_id, consumer) for consumer in consumers
                ),
                "shared_object_ids": sorted(set(shared_object_ids)),
            },
        )

    return transformed, unmodelled


def load_shares(
    neo4j_session: neo4j.Session,
    shares: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeShareSchema(),
        shares,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeShareSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync shares, the objects they expose and the accounts they reach.

    Runs after the data hierarchy and the managed accounts so both ends of every edge
    are already in the graph.

    Returns whether every share could be read. When one could not, the caller skips
    share cleanup so previously collected shares are not deleted.
    """
    shares = get_shares(client)
    if shares is None:
        return False

    complete = True
    grants_by_share: dict[str, list[dict[str, Any]]] = {}
    consumers_by_share: dict[str, list[dict[str, Any]]] = {}
    for share in shares:
        name = share["name"]
        if to_text(share.get("kind")) != _OUTBOUND:
            continue
        grants = get_share_grants(client, name)
        if grants is None:
            complete = False
        else:
            grants_by_share[name] = grants

        consumers = get_share_consumers(client, name)
        if consumers is None:
            complete = False
        else:
            consumers_by_share[name] = consumers

    transformed, unmodelled = transform(
        shares, grants_by_share, consumers_by_share, client.account_id
    )
    if unmodelled:
        logger.info(
            "Skipped %d objects exposed by Snowflake shares whose object type "
            "Cartography does not model.",
            unmodelled,
        )
    logger.info(
        "Loading %d Snowflake shares for account %s.",
        len(transformed),
        client.account_id,
    )
    load_shares(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )

    if not complete:
        logger.warning(
            "Some Snowflake shares could not be read in full; skipping share cleanup "
            "so still-valid shares are not deleted.",
        )
    return complete
