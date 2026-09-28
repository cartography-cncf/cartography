"""Snowflake replication and failover groups.

Both are account-to-account data movement with no REST endpoint, so they come from
``SHOW REPLICATION GROUPS`` and ``SHOW FAILOVER GROUPS``. The two statements return
the same columns, so one transform serves both and only the target label differs.

Replication needs Enterprise and failover needs Business Critical, so either
statement can legitimately fail on a lower edition. Whichever statement did answer
is still loaded, and the module only reports itself complete when both did, so a
partial read never leads to cleanup deleting the other kind.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import name_list
from cartography.intel.snowflake.sql_values import to_bool
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import normalize_account_id
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.replication_group import SnowflakeFailoverGroupSchema
from cartography.models.snowflake.replication_group import (
    SnowflakeReplicationGroupSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_replication_groups(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every replication group, or None when the edition or role forbids it."""
    try:
        return client.run_sql("SHOW REPLICATION GROUPS")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "replication groups",
            "SHOW REPLICATION GROUPS is not available on this account edition",
        )
        return None


@timeit
def get_failover_groups(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every failover group, or None when the edition or role forbids it."""
    try:
        return client.run_sql("SHOW FAILOVER GROUPS")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "failover groups",
            "SHOW FAILOVER GROUPS is not available on this account edition",
        )
        return None


def _target_account_id(allowed_account: str) -> str | None:
    """Resolve an allowed-account entry to an account node id.

    Snowflake writes these organization-qualified, which is the same identifier the
    account nodes are keyed on once it is normalised. An entry that is not
    organization-qualified cannot name an account node, so it stays in the raw list
    only.
    """
    try:
        return normalize_account_id(allowed_account)
    except ValueError:
        return None


def transform(
    groups: list[dict[str, Any]],
    object_type: str,
    account_id: str,
) -> list[dict[str, Any]]:
    """Shape replication or failover group rows into nodes.

    ``object_type`` is the key segment used in the node id, which is what makes a
    replication group and a failover group of the same name distinct nodes.
    """
    transformed: list[dict[str, Any]] = []

    for group in groups:
        name = group["name"]
        allowed_accounts = name_list(group.get("allowed_accounts"))
        allowed_databases = name_list(group.get("allowed_databases"))
        transformed.append(
            {
                "id": sf_id(account_id, object_type, sf_fqn(name)),
                "name": name,
                "group_type": to_text(group.get("type")),
                "is_primary": to_bool(group.get("is_primary")),
                "primary": to_text(group.get("primary")),
                "object_types": name_list(group.get("object_types")),
                "allowed_integration_types": name_list(
                    group.get("allowed_integration_types"),
                ),
                "allowed_accounts": allowed_accounts,
                "allowed_account_ids": sorted(
                    {
                        target
                        for entry in allowed_accounts
                        for target in [_target_account_id(entry)]
                        if target
                    },
                ),
                "allowed_databases": allowed_databases,
                "allowed_database_ids": sorted(
                    {
                        sf_id(account_id, "database", sf_fqn(database))
                        for database in allowed_databases
                    },
                ),
                "allowed_shares": name_list(group.get("allowed_shares")),
                "replication_schedule": to_text(group.get("replication_schedule")),
                "secondary_state": to_text(group.get("secondary_state")),
                "next_scheduled_refresh": iso_to_datetime(
                    group.get("next_scheduled_refresh"),
                ),
                "owner": to_text(group.get("owner")),
                "comment": to_text(group.get("comment")),
                "created_on": iso_to_datetime(group.get("created_on")),
            },
        )

    return transformed


def load_replication_groups(
    neo4j_session: neo4j.Session,
    replication_groups: list[dict[str, Any]],
    failover_groups: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeReplicationGroupSchema(),
        replication_groups,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        neo4j_session,
        SnowflakeFailoverGroupSchema(),
        failover_groups,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeReplicationGroupSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        SnowflakeFailoverGroupSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync replication and failover groups.

    Runs after the databases and the accounts so both ends of every edge are already
    in the graph.

    Returns whether both listings could be read. When one could not, the caller skips
    cleanup so previously collected groups are not deleted.
    """
    replication_groups = get_replication_groups(client)
    failover_groups = get_failover_groups(client)

    transformed_replication = (
        transform(replication_groups, "replication_group", client.account_id)
        if replication_groups is not None
        else []
    )
    transformed_failover = (
        transform(failover_groups, "failover_group", client.account_id)
        if failover_groups is not None
        else []
    )
    logger.info(
        "Loading %d Snowflake replication groups and %d failover groups for account %s.",
        len(transformed_replication),
        len(transformed_failover),
        client.account_id,
    )
    load_replication_groups(
        neo4j_session,
        transformed_replication,
        transformed_failover,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return replication_groups is not None and failover_groups is not None
