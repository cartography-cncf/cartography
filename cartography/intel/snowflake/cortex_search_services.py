"""Snowflake Cortex Search services: managed semantic indexes over account data."""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import name_list
from cartography.intel.snowflake.names import schema_object_fqn
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.cortex_search_service import (
    SnowflakeCortexSearchServiceSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Cortex Search services in one schema, or None when the schema is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}"
            "/cortex-search-services",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


def transform(
    services: list[dict[str, Any]],
    schema: dict[str, Any],
    account_id: str,
) -> list[dict[str, Any]]:
    database_name = schema["database_name"]
    schema_name = schema["name"]
    transformed: list[dict[str, Any]] = []

    for service in services:
        name = service["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        warehouse = service.get("warehouse")
        # A service can be defined over a query rather than a single table, in
        # which case there is no object name to resolve and the edge is suppressed.
        source = service.get("source")
        source_fqn = schema_object_fqn(database_name, schema_name, source)
        transformed.append(
            {
                "id": sf_id(account_id, "cortex_search_service", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": schema["id"],
                "target_lag": service.get("target_lag"),
                "warehouse": warehouse,
                "warehouse_id": (
                    sf_id(account_id, "warehouse", sf_fqn(warehouse))
                    if warehouse
                    else None
                ),
                "source": source,
                "source_table_id": (
                    sf_id(account_id, "table", source_fqn) if source_fqn else None
                ),
                "embedding_model": service.get("embedding_model"),
                "attribute_columns": name_list(service.get("attribute_columns")),
                "search_column": service.get("search_column"),
                "service_query_url": service.get("service_query_url"),
                "comment": service.get("comment"),
                "created_on": iso_to_datetime(service.get("created_on")),
            },
        )
    return transformed


def load_cortex_search_services(
    neo4j_session: neo4j.Session,
    services: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeCortexSearchServiceSchema(),
        services,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeCortexSearchServiceSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync every Cortex Search service in every readable schema.

    Returns whether the walk was complete, so the caller can skip cleanup rather
    than deleting nodes it merely failed to re-read this run.
    """
    account_id = client.account_id
    services: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        listing = get(client, schema["database_name"], schema["name"])
        if listing is None:
            complete = False
            continue
        services.extend(transform(listing, schema, account_id))

    logger.info(
        "Loading %d Snowflake Cortex Search services for account %s.",
        len(services),
        account_id,
    )
    load_cortex_search_services(
        neo4j_session, services, account_id, common_job_parameters["UPDATE_TAG"]
    )

    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be read for Cortex Search services; "
            "skipping their cleanup so still-valid nodes are not deleted.",
        )
    return complete
