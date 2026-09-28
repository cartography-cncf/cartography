"""Snowflake external tables, read through the SQL API.

The object API has no external-table endpoint, so this walks
``SHOW EXTERNAL TABLES IN DATABASE`` once per database. An external table's rows never
enter Snowflake storage: they are parsed out of files in a cloud bucket on every
query, so the stage and the file format are what turn the table into storage access.

Every value the SQL API returns is a string keyed by the lowercased column name, so
booleans are coerced here.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import split_qualified_name
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.external_table import SnowflakeExternalTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _reference_id(
    reference: str | None, object_type: str, account_id: str
) -> str | None:
    """Resolve a fully-qualified object reference to that object's node id.

    ``SHOW EXTERNAL TABLES`` reports the stage and the file format as plain dotted
    text, quoting only the components that need it, and prefixes a stage reference
    with ``@``. Splitting is quote-aware, so a dot inside a quoted component stays
    part of the name instead of being read as a separator. A reference that is not a
    three-part name stays unresolved and the caller draws no edge rather than
    pointing one at the wrong object.
    """
    if not reference:
        return None
    parts = split_qualified_name(reference.lstrip("@"))
    if len(parts) != 3 or any(not part for part in parts):
        return None
    return sf_id(account_id, object_type, sf_fqn(*parts))


@timeit
def get_database_external_tables(
    client: SnowflakeClient, database_name: str
) -> list[dict[str, Any]] | None:
    """External tables of one database, or None when the statement is unavailable."""
    try:
        return client.run_sql(
            f"SHOW EXTERNAL TABLES IN DATABASE {sf_fqn(database_name)}",
        )
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            f"external tables in database {database_name}",
            "SHOW EXTERNAL TABLES is not supported or not permitted",
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return every readable external table plus whether every database was read.

    ``SHOW EXTERNAL TABLES`` is scoped to a database, so the databases to walk are the
    distinct parents of the schemas already synced.
    """
    rows: list[dict[str, Any]] = []
    complete = True
    for database_name in sorted({schema["database_name"] for schema in schemas}):
        database_rows = get_database_external_tables(client, database_name)
        if database_rows is None:
            complete = False
            continue
        rows.extend(database_rows)
    return rows, complete


def transform(
    external_tables: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for external_table in external_tables:
        database_name = external_table["database_name"]
        schema_name = external_table["schema_name"]
        name = external_table["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        stage = external_table.get("stage") or None
        file_format_name = external_table.get("file_format_name") or None
        transformed.append(
            {
                "id": sf_id(account_id, "external_table", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                "stage": stage,
                # Null when the reference cannot be resolved, which suppresses the
                # edge instead of pointing it at nothing.
                "stage_id": _reference_id(stage, "stage", account_id),
                "location": external_table.get("location") or None,
                "cloud": external_table.get("cloud") or None,
                "region": external_table.get("region") or None,
                "file_format_name": file_format_name,
                "file_format_id": _reference_id(
                    file_format_name, "file_format", account_id
                ),
                "file_format_type": external_table.get("file_format_type") or None,
                "table_format": external_table.get("table_format") or None,
                "notification_channel": external_table.get("notification_channel")
                or None,
                "invalid": str(external_table.get("invalid")).lower() == "true",
                "invalid_reason": external_table.get("invalid_reason") or None,
                "owner": external_table.get("owner") or None,
                "owner_role_type": external_table.get("owner_role_type") or None,
                "comment": external_table.get("comment") or None,
                "last_refreshed_on": iso_to_datetime(
                    external_table.get("last_refreshed_on")
                ),
                "created_on": iso_to_datetime(external_table.get("created_on")),
            },
        )
    return transformed


def load_external_tables(
    neo4j_session: neo4j.Session,
    external_tables: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeExternalTableSchema(),
        external_tables,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeExternalTableSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake external tables, returning whether every database was read."""
    rows, complete = get(client, schemas)
    external_tables = transform(rows, client.account_id)
    logger.info(
        "Loading %d Snowflake external tables for account %s.",
        len(external_tables),
        client.account_id,
    )
    load_external_tables(
        neo4j_session,
        external_tables,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if not complete:
        logger.warning(
            "Some Snowflake databases could not be read for external tables; "
            "skipping their cleanup so still-valid nodes are not deleted.",
        )
    return complete
