"""Snowflake tables, where the account's data actually sits.

Tables are listed per schema. A 403 or 404 on one schema is recorded as incomplete
rather than fatal, so a collector role missing ``USAGE`` on a single schema does not
cost the whole account.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.table import SnowflakeTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_schema_tables(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Tables of one schema, or None when the role cannot read that schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/tables",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list tables of Snowflake schema %s.%s (permission denied); they "
            "will be missing from the graph.",
            database_name,
            schema_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return every readable table plus whether every schema could be read."""
    tables: list[dict[str, Any]] = []
    complete = True
    for schema in schemas:
        rows = get_schema_tables(client, schema["database_name"], schema["name"])
        if rows is None:
            complete = False
            continue
        tables.extend(rows)
    return tables, complete


def transform(tables: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    """Shape table rows, dropping the column payload.

    A node per column would outnumber every other node in the graph by orders of
    magnitude while answering no security question the column count does not, so
    only the count is kept.
    """
    transformed: list[dict[str, Any]] = []
    for table in tables:
        database_name = table["database_name"]
        schema_name = table["schema_name"]
        name = table["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        columns = table.get("columns")
        transformed.append(
            {
                "id": sf_id(account_id, "table", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                "kind": table.get("kind"),
                "table_type": table.get("table_type"),
                "row_count": table.get("rows"),
                "size_bytes": table.get("bytes"),
                "column_count": len(columns) if columns is not None else None,
                "owner": table.get("owner"),
                "owner_role_type": table.get("owner_role_type"),
                "comment": table.get("comment"),
                "cluster_by": table.get("cluster_by") or None,
                "change_tracking": table.get("change_tracking"),
                "enable_schema_evolution": table.get("enable_schema_evolution"),
                "search_optimization": table.get("search_optimization"),
                "data_retention_time_in_days": table.get("data_retention_time_in_days"),
                "created_on": iso_to_datetime(table.get("created_on")),
                "dropped_on": iso_to_datetime(table.get("dropped_on")),
            },
        )
    return transformed


def load_tables(
    neo4j_session: neo4j.Session,
    tables: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeTableSchema(),
        tables,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeTableSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake tables, returning whether every schema could be read."""
    raw_tables, complete = get(client, schemas)
    tables = transform(raw_tables, client.account_id)
    logger.info(
        "Loading %d Snowflake tables for account %s.", len(tables), client.account_id
    )
    load_tables(
        neo4j_session, tables, client.account_id, common_job_parameters["UPDATE_TAG"]
    )
    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be listed; skipping table cleanup so "
            "still-valid tables are not deleted.",
        )
    return complete
