"""Snowflake dynamic tables: declarative pipelines Snowflake refreshes on a lag target.

A refresh runs with the dynamic table owner's privileges on the warehouse the table
names, so the USES_WAREHOUSE edge is what connects a pipeline to the compute it
spends.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import schedule_to_text
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.dynamic_table import SnowflakeDynamicTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_schema_dynamic_tables(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Dynamic tables of one schema, or None when the role cannot read the schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/dynamic-tables",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list dynamic tables of Snowflake schema %s.%s (permission "
            "denied); they will be missing from the graph.",
            database_name,
            schema_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return one entry per readable schema, plus whether every schema was read.

    Unlike the table and view endpoints, the dynamic-table payload does not repeat
    its database and schema, so each listing is returned alongside the parent it was
    fetched for. That parent is what the qualified name and the parent schema id are
    built from.
    """
    listings: list[dict[str, Any]] = []
    complete = True
    for schema in schemas:
        database_name = schema["database_name"]
        schema_name = schema["name"]
        rows = get_schema_dynamic_tables(client, database_name, schema_name)
        if rows is None:
            complete = False
            continue
        listings.append(
            {
                "database_name": database_name,
                "schema_name": schema_name,
                "dynamic_tables": rows,
            },
        )
    return listings, complete


def transform(listings: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for listing in listings:
        database_name = listing["database_name"]
        schema_name = listing["schema_name"]
        parent_schema_id = sf_id(
            account_id, "schema", sf_fqn(database_name, schema_name)
        )
        for dynamic_table in listing["dynamic_tables"]:
            name = dynamic_table["name"]
            qualified_name = sf_fqn(database_name, schema_name, name)
            warehouse = dynamic_table.get("warehouse") or None
            transformed.append(
                {
                    "id": sf_id(account_id, "dynamic_table", qualified_name),
                    "name": name,
                    "qualified_name": qualified_name,
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "parent_schema_id": parent_schema_id,
                    "warehouse": warehouse,
                    # Null when no warehouse is reported, which suppresses the
                    # USES_WAREHOUSE edge instead of pointing it at nothing.
                    "warehouse_id": (
                        sf_id(account_id, "warehouse", sf_fqn(warehouse))
                        if warehouse
                        else None
                    ),
                    "target_lag": schedule_to_text(dynamic_table.get("target_lag")),
                    "refresh_mode": dynamic_table.get("refresh_mode"),
                    "scheduling_state": dynamic_table.get("scheduling_state"),
                    "query": dynamic_table.get("query"),
                    "owner": dynamic_table.get("owner"),
                    "comment": dynamic_table.get("comment"),
                    "created_on": iso_to_datetime(dynamic_table.get("created_on")),
                },
            )
    return transformed


def load_dynamic_tables(
    neo4j_session: neo4j.Session,
    dynamic_tables: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeDynamicTableSchema(),
        dynamic_tables,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeDynamicTableSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake dynamic tables, returning whether every schema could be read."""
    listings, complete = get(client, schemas)
    dynamic_tables = transform(listings, client.account_id)
    logger.info(
        "Loading %d Snowflake dynamic tables for account %s.",
        len(dynamic_tables),
        client.account_id,
    )
    load_dynamic_tables(
        neo4j_session,
        dynamic_tables,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be listed; skipping dynamic table "
            "cleanup so still-valid dynamic tables are not deleted.",
        )
    return complete
