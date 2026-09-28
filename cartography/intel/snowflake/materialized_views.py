"""Snowflake materialized views, read through the SQL API.

The object API has no materialized-view endpoint, so this walks
``SHOW MATERIALIZED VIEWS IN DATABASE`` once per database. Materialized views are an
Enterprise-edition feature, so the statement itself can be unavailable; that is
reported as incomplete rather than fatal so the rest of the sync still lands.

Every value the SQL API returns is a string keyed by the lowercased column name, so
booleans and counts are coerced here.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.materialized_view import (
    SnowflakeMaterializedViewSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _to_bool(value: Any) -> bool:
    """Coerce a SHOW output cell to a boolean."""
    return str(value).lower() == "true"


def _to_int(value: Any) -> int | None:
    """Coerce a SHOW output cell to an integer, or None when it is not numeric."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None


@timeit
def get_database_materialized_views(
    client: SnowflakeClient, database_name: str
) -> list[dict[str, Any]] | None:
    """Materialized views of one database, or None when the statement is unavailable."""
    try:
        return client.run_sql(
            f"SHOW MATERIALIZED VIEWS IN DATABASE {sf_fqn(database_name)}",
        )
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            f"materialized views in database {database_name}",
            "SHOW MATERIALIZED VIEWS is not supported or not permitted",
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return every readable materialized view plus whether every database was read.

    ``SHOW MATERIALIZED VIEWS`` is scoped to a database, so the databases to walk are
    the distinct parents of the schemas already synced.
    """
    rows: list[dict[str, Any]] = []
    complete = True
    for database_name in sorted({schema["database_name"] for schema in schemas}):
        database_rows = get_database_materialized_views(client, database_name)
        if database_rows is None:
            complete = False
            continue
        rows.extend(database_rows)
    return rows, complete


def transform(
    materialized_views: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for materialized_view in materialized_views:
        database_name = materialized_view["database_name"]
        schema_name = materialized_view["schema_name"]
        name = materialized_view["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        transformed.append(
            {
                "id": sf_id(account_id, "materialized_view", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                "is_secure": _to_bool(materialized_view.get("is_secure")),
                "query": materialized_view.get("text"),
                "source_name": materialized_view.get("source") or None,
                "source_database_name": materialized_view.get("source_database_name")
                or None,
                "source_schema_name": materialized_view.get("source_schema_name")
                or None,
                "row_count": _to_int(materialized_view.get("rows")),
                "size_bytes": _to_int(materialized_view.get("bytes")),
                "cluster_by": materialized_view.get("cluster_by") or None,
                "automatic_clustering": _to_bool(
                    materialized_view.get("automatic_clustering")
                ),
                "invalid": _to_bool(materialized_view.get("invalid")),
                "invalid_reason": materialized_view.get("invalid_reason") or None,
                "owner": materialized_view.get("owner") or None,
                "owner_role_type": materialized_view.get("owner_role_type") or None,
                "comment": materialized_view.get("comment") or None,
                "refreshed_on": iso_to_datetime(materialized_view.get("refreshed_on")),
                "created_on": iso_to_datetime(materialized_view.get("created_on")),
            },
        )
    return transformed


def load_materialized_views(
    neo4j_session: neo4j.Session,
    materialized_views: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeMaterializedViewSchema(),
        materialized_views,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeMaterializedViewSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake materialized views, returning whether every database was read."""
    rows, complete = get(client, schemas)
    materialized_views = transform(rows, client.account_id)
    logger.info(
        "Loading %d Snowflake materialized views for account %s.",
        len(materialized_views),
        client.account_id,
    )
    load_materialized_views(
        neo4j_session,
        materialized_views,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if not complete:
        logger.warning(
            "Some Snowflake databases could not be read for materialized views; "
            "skipping their cleanup so still-valid nodes are not deleted.",
        )
    return complete
