"""Snowflake Iceberg tables, whose files sit on customer-owned cloud storage.

An Iceberg table is the point where Snowflake's access control stops being the only
thing protecting the data: the files live on an external volume, so whoever can read
that bucket can read the table. The STORED_IN edge is what makes that reachable in
the graph.
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
from cartography.models.snowflake.iceberg_table import SnowflakeIcebergTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Snowflake reports its own internal catalog as the literal name "SNOWFLAKE". That
# is not a catalog integration object, so no USES_CATALOG edge should be drawn.
INTERNAL_CATALOG = "SNOWFLAKE"


@timeit
def get_schema_iceberg_tables(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Iceberg tables of one schema, or None when the role cannot read the schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/iceberg-tables",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list Iceberg tables of Snowflake schema %s.%s (permission "
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

    The Iceberg-table payload does not repeat its database and schema, so each
    listing is returned alongside the parent it was fetched for.
    """
    listings: list[dict[str, Any]] = []
    complete = True
    for schema in schemas:
        database_name = schema["database_name"]
        schema_name = schema["name"]
        rows = get_schema_iceberg_tables(client, database_name, schema_name)
        if rows is None:
            complete = False
            continue
        listings.append(
            {
                "database_name": database_name,
                "schema_name": schema_name,
                "iceberg_tables": rows,
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
        for iceberg_table in listing["iceberg_tables"]:
            name = iceberg_table["name"]
            qualified_name = sf_fqn(database_name, schema_name, name)
            external_volume = iceberg_table.get("external_volume") or None
            catalog = iceberg_table.get("catalog") or None
            # The internal Snowflake catalog is not an integration object, so it has
            # no node to point a catalog edge at.
            catalog_integration = catalog if catalog != INTERNAL_CATALOG else None
            transformed.append(
                {
                    "id": sf_id(account_id, "iceberg_table", qualified_name),
                    "name": name,
                    "qualified_name": qualified_name,
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "parent_schema_id": parent_schema_id,
                    "external_volume": external_volume,
                    # Null when no volume is reported, which suppresses the STORED_IN
                    # edge instead of pointing it at nothing.
                    "external_volume_id": (
                        sf_id(account_id, "external_volume", sf_fqn(external_volume))
                        if external_volume
                        else None
                    ),
                    "catalog": catalog,
                    "catalog_integration_id": (
                        sf_id(
                            account_id,
                            "catalog_integration",
                            sf_fqn(catalog_integration),
                        )
                        if catalog_integration
                        else None
                    ),
                    "catalog_sync": iceberg_table.get("catalog_sync") or None,
                    "catalog_table_name": iceberg_table.get("catalog_table_name"),
                    "catalog_namespace": iceberg_table.get("catalog_namespace"),
                    "base_location": iceberg_table.get("base_location"),
                    "iceberg_table_type": iceberg_table.get("iceberg_table_type"),
                    "storage_serialization_policy": iceberg_table.get(
                        "storage_serialization_policy"
                    ),
                    "can_write_metadata": iceberg_table.get("can_write_metadata"),
                    "owner": iceberg_table.get("owner"),
                    "created_on": iso_to_datetime(iceberg_table.get("created_on")),
                },
            )
    return transformed


def load_iceberg_tables(
    neo4j_session: neo4j.Session,
    iceberg_tables: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeIcebergTableSchema(),
        iceberg_tables,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeIcebergTableSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake Iceberg tables, returning whether every schema could be read."""
    listings, complete = get(client, schemas)
    iceberg_tables = transform(listings, client.account_id)
    logger.info(
        "Loading %d Snowflake Iceberg tables for account %s.",
        len(iceberg_tables),
        client.account_id,
    )
    load_iceberg_tables(
        neo4j_session,
        iceberg_tables,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be listed; skipping Iceberg table "
            "cleanup so still-valid Iceberg tables are not deleted.",
        )
    return complete
