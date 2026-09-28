"""Snowflake databases, the roots of the data hierarchy.

Everything under a database is fetched per parent, so this module decides how much
of the account the rest of the data-hierarchy syncs walk. Databases that a
collector role realistically cannot read are skipped up front, with a reason
logged, rather than producing a wall of 403 warnings downstream.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import share_key_from_origin
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.database import SnowflakeDatabaseSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# SNOWFLAKE holds Snowflake's own metadata views and SNOWFLAKE_SAMPLE_DATA is a
# read-only sample share every account gets. Neither is customer data, both are
# large, and listing their schemas needs privileges a collector role usually does
# not have.
DEFAULT_SKIPPED_DATABASES = frozenset({"SNOWFLAKE", "SNOWFLAKE_SAMPLE_DATA"})


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]]:
    """List every database in the account."""
    return client.list_all("/api/v2/databases")


def _skip_walk_reason(database: dict[str, Any], allowed: set[str] | None) -> str | None:
    """Why this database's schemas should not be walked, or None to walk it.

    This gates the *walk*, not the inventory. Every database is still loaded as a
    node, because a database mounted from an inbound share is a security-relevant
    fact in its own right: it is external data arriving in the account, and
    dropping it would hide that. Only the descent into its schemas is skipped.
    """
    name = database["name"]
    if allowed is not None:
        # An explicit allowlist is exhaustive, so an operator can deliberately
        # include Snowflake's own databases or a shared one.
        #
        # Matched case-insensitively: Snowflake returns an unquoted identifier
        # upper-cased but preserves the case of a quoted one, and the operator has
        # no way to signal which they meant, so both spellings have to match.
        if name.casefold() not in {allowed_name.casefold() for allowed_name in allowed}:
            return "it is not in the configured database allowlist"
        return None
    if name in DEFAULT_SKIPPED_DATABASES:
        return "it holds Snowflake-managed data rather than the account's own"
    if database.get("origin"):
        return (
            f"it is mounted from inbound share {database['origin']}, whose schemas "
            "this role cannot list"
        )
    return None


def transform(databases: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for database in databases:
        name = database["name"]
        qualified_name = sf_fqn(name)
        origin = database.get("origin") or None
        transformed.append(
            {
                "id": sf_id(account_id, "database", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "kind": database.get("kind"),
                "origin": origin,
                "is_from_share": origin is not None,
                # `origin` is a PROVIDER_ACCOUNT.SHARE_NAME reference. It goes through
                # the same share_key() the shares sync uses, so the id matches the
                # share's own however each side qualifies the provider account. Null
                # when the database is local, which suppresses the CREATED_FROM_SHARE
                # edge instead of pointing it at nothing.
                "share_id": (
                    sf_id(account_id, "share", share_qualified_name)
                    if (share_qualified_name := share_key_from_origin(origin))
                    else None
                ),
                "owner": database.get("owner"),
                "owner_role_type": database.get("owner_role_type"),
                "comment": database.get("comment"),
                "options": database.get("options"),
                "retention_time": database.get("retention_time"),
                "data_retention_time_in_days": database.get(
                    "data_retention_time_in_days"
                ),
                "budget": database.get("budget"),
                "is_current": database.get("is_current"),
                "is_default": database.get("is_default"),
                "created_on": iso_to_datetime(database.get("created_on")),
                "dropped_on": iso_to_datetime(database.get("dropped_on")),
            },
        )
    return transformed


def load_databases(
    neo4j_session: neo4j.Session,
    databases: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeDatabaseSchema(),
        databases,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeDatabaseSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    allowed_databases: set[str] | None,
    common_job_parameters: dict,
) -> tuple[list[dict[str, Any]], bool]:
    """Sync every database, returning only the ones whose schemas should be walked.

    Returns ``(walkable databases, complete)``. All databases are loaded as nodes
    so the inventory is complete, but Snowflake-managed and inbound-share databases
    are excluded from the returned list: descending into them answers 403 for all
    but the most privileged roles, and their contents are the provider's data
    rather than the account's.

    The database listing is a single account-level request, so it either succeeds
    outright or raises: ``complete`` is therefore always True here, and exists so
    every data-hierarchy sync reports completeness the same way.
    """
    raw_databases = get(client)
    databases = transform(raw_databases, client.account_id)
    logger.info(
        "Loading %d Snowflake databases for account %s.",
        len(databases),
        client.account_id,
    )
    load_databases(
        neo4j_session, databases, client.account_id, common_job_parameters["UPDATE_TAG"]
    )

    skip_reasons = {
        database["name"]: _skip_walk_reason(database, allowed_databases)
        for database in raw_databases
    }
    for name, reason in skip_reasons.items():
        if reason:
            logger.info("Not walking Snowflake database %s: %s.", name, reason)
    walkable = [
        database for database in databases if not skip_reasons.get(database["name"])
    ]
    return walkable, True
