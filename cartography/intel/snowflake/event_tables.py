"""Snowflake event tables, the destination for logs, traces and metrics.

Event tables collect whatever an application chose to log, so they routinely hold
data that never appears in the modelled schema. Their size is the useful signal.
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
from cartography.models.snowflake.event_table import SnowflakeEventTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_schema_event_tables(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Event tables of one schema, or None when the role cannot read the schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/event-tables",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list event tables of Snowflake schema %s.%s (permission denied); "
            "they will be missing from the graph.",
            database_name,
            schema_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return one entry per readable schema, plus whether every schema was read.

    The event-table payload does not repeat its database and schema, so each listing
    is returned alongside the parent it was fetched for.
    """
    listings: list[dict[str, Any]] = []
    complete = True
    for schema in schemas:
        database_name = schema["database_name"]
        schema_name = schema["name"]
        rows = get_schema_event_tables(client, database_name, schema_name)
        if rows is None:
            complete = False
            continue
        listings.append(
            {
                "database_name": database_name,
                "schema_name": schema_name,
                "event_tables": rows,
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
        for event_table in listing["event_tables"]:
            name = event_table["name"]
            qualified_name = sf_fqn(database_name, schema_name, name)
            transformed.append(
                {
                    "id": sf_id(account_id, "event_table", qualified_name),
                    "name": name,
                    "qualified_name": qualified_name,
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "parent_schema_id": parent_schema_id,
                    "row_count": event_table.get("rows"),
                    "size_bytes": event_table.get("bytes"),
                    "owner": event_table.get("owner"),
                    "comment": event_table.get("comment"),
                    "created_on": iso_to_datetime(event_table.get("created_on")),
                },
            )
    return transformed


def load_event_tables(
    neo4j_session: neo4j.Session,
    event_tables: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeEventTableSchema(),
        event_tables,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeEventTableSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake event tables, returning whether every schema could be read."""
    listings, complete = get(client, schemas)
    event_tables = transform(listings, client.account_id)
    logger.info(
        "Loading %d Snowflake event tables for account %s.",
        len(event_tables),
        client.account_id,
    )
    load_event_tables(
        neo4j_session,
        event_tables,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be listed; skipping event table "
            "cleanup so still-valid event tables are not deleted.",
        )
    return complete
