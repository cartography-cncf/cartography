"""Snowflake schemas, the namespaces every table, view and stream lives in.

Schemas are listed per database. A collector role without ``USAGE`` on one
database must not fail the whole sync, so a 403 or 404 on a single database is
recorded as incomplete and the caller skips cleanup instead of deleting schemas it
merely failed to re-read.
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
from cartography.models.snowflake.schema import SnowflakeSchemaSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_database_schemas(
    client: SnowflakeClient, database_name: str
) -> list[dict[str, Any]] | None:
    """Schemas of one database, or None when the role cannot read that database."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas"
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list schemas of Snowflake database %s (permission denied); its "
            "contents will be missing from the graph.",
            database_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, databases: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return every readable schema plus whether every database could be read."""
    schemas: list[dict[str, Any]] = []
    complete = True
    for database in databases:
        rows = get_database_schemas(client, database["name"])
        if rows is None:
            complete = False
            continue
        schemas.extend(rows)
    return schemas, complete


def transform(schemas: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for schema in schemas:
        database_name = schema["database_name"]
        name = schema["name"]
        qualified_name = sf_fqn(database_name, name)
        external_volume = schema.get("external_volume") or None
        transformed.append(
            {
                "id": sf_id(account_id, "schema", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "parent_database_id": sf_id(
                    account_id, "database", sf_fqn(database_name)
                ),
                "kind": schema.get("kind"),
                "managed_access": schema.get("managed_access"),
                "owner": schema.get("owner"),
                "owner_role_type": schema.get("owner_role_type"),
                "comment": schema.get("comment"),
                "options": schema.get("options"),
                "retention_time": schema.get("retention_time"),
                "external_volume": external_volume,
                # Null when the schema has no default volume, which suppresses the
                # DEFAULT_EXTERNAL_VOLUME edge instead of pointing it at nothing.
                "external_volume_id": (
                    sf_id(account_id, "external_volume", sf_fqn(external_volume))
                    if external_volume
                    else None
                ),
                "catalog": schema.get("catalog") or None,
                "created_on": iso_to_datetime(schema.get("created_on")),
                "dropped_on": iso_to_datetime(schema.get("dropped_on")),
            },
        )
    return transformed


def load_schemas(
    neo4j_session: neo4j.Session,
    schemas: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeSchemaSchema(),
        schemas,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeSchemaSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    databases: list[dict[str, Any]],
    common_job_parameters: dict,
) -> tuple[list[dict[str, Any]], bool]:
    """Sync Snowflake schemas and return them for the object-level syncs to walk.

    Returns ``(schemas, complete)``, where ``complete`` is False when any database
    could not be listed.
    """
    raw_schemas, complete = get(client, databases)
    schemas = transform(raw_schemas, client.account_id)
    logger.info(
        "Loading %d Snowflake schemas for account %s.", len(schemas), client.account_id
    )
    load_schemas(
        neo4j_session, schemas, client.account_id, common_job_parameters["UPDATE_TAG"]
    )
    if not complete:
        logger.warning(
            "Some Snowflake databases could not be listed; skipping schema cleanup "
            "so still-valid schemas are not deleted.",
        )
    return schemas, complete
