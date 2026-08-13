"""Snowflake named file formats, read through the SQL API.

The object API has no file-format endpoint, so this walks
``SHOW FILE FORMATS IN DATABASE`` once per database. File formats are what external
tables and COPY statements name to parse staged files, and they are grantable objects
in their own right.

Every value the SQL API returns is a string keyed by the lowercased column name.
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
from cartography.models.snowflake.file_format import SnowflakeFileFormatSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_database_file_formats(
    client: SnowflakeClient, database_name: str
) -> list[dict[str, Any]] | None:
    """File formats of one database, or None when the statement is unavailable."""
    try:
        return client.run_sql(
            f"SHOW FILE FORMATS IN DATABASE {sf_fqn(database_name)}",
        )
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            f"file formats in database {database_name}",
            "SHOW FILE FORMATS is not supported or not permitted",
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return every readable file format plus whether every database was read.

    ``SHOW FILE FORMATS`` is scoped to a database, so the databases to walk are the
    distinct parents of the schemas already synced.
    """
    rows: list[dict[str, Any]] = []
    complete = True
    for database_name in sorted({schema["database_name"] for schema in schemas}):
        database_rows = get_database_file_formats(client, database_name)
        if database_rows is None:
            complete = False
            continue
        rows.extend(database_rows)
    return rows, complete


def transform(
    file_formats: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for file_format in file_formats:
        database_name = file_format["database_name"]
        schema_name = file_format["schema_name"]
        name = file_format["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        transformed.append(
            {
                "id": sf_id(account_id, "file_format", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                "format_type": file_format.get("type") or None,
                "format_options": file_format.get("format_options") or None,
                "owner": file_format.get("owner") or None,
                "owner_role_type": file_format.get("owner_role_type") or None,
                "comment": file_format.get("comment") or None,
                "created_on": iso_to_datetime(file_format.get("created_on")),
            },
        )
    return transformed


def load_file_formats(
    neo4j_session: neo4j.Session,
    file_formats: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeFileFormatSchema(),
        file_formats,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeFileFormatSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake file formats, returning whether every database was read."""
    rows, complete = get(client, schemas)
    file_formats = transform(rows, client.account_id)
    logger.info(
        "Loading %d Snowflake file formats for account %s.",
        len(file_formats),
        client.account_id,
    )
    load_file_formats(
        neo4j_session,
        file_formats,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if not complete:
        logger.warning(
            "Some Snowflake databases could not be read for file formats; skipping "
            "their cleanup so still-valid nodes are not deleted.",
        )
    return complete
