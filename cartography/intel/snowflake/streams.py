"""Snowflake streams, the change-data feeds over tables, views and stages.

A stream is a second door onto its source's rows: SELECT on the stream returns the
source's changed data, so the READS_FROM edge is what shows that a privilege on the
stream reaches the table behind it.
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
from cartography.models.snowflake.stream import SnowflakeStreamSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _source_type(stream: dict[str, Any]) -> str | None:
    """Return what kind of object the stream reads from.

    The object API reports the source as a nested object whose ``src_type`` is the
    discriminator (``table``, ``view``, ``stage``, ...), while older responses used
    a flat ``source_type`` string. Neo4j properties must be primitives, so only the
    discriminator is kept; the source's identity is already carried by
    ``source_name`` and resolved into ``source_table_id``.
    """
    source = stream.get("stream_source")
    if isinstance(source, dict):
        return source.get("src_type") or source.get("source_type")
    return source or stream.get("source_type")


def _source_name(stream: dict[str, Any]) -> str | None:
    """Return the stream's source object as a dotted reference.

    The object API nests the source's identity under ``stream_source`` with its
    database and schema alongside the name, so the qualified reference is rebuilt
    from those parts. Older responses carried a flat ``table_name`` instead, which
    is still accepted.
    """
    source = stream.get("stream_source")
    if isinstance(source, dict):
        name = source.get("name")
        if not name:
            return None
        parts = [
            part
            for part in (
                source.get("database_name"),
                source.get("schema_name"),
                name,
            )
            if part
        ]
        return ".".join(parts)
    return stream.get("table_name") or None


def _source_table_id(
    table_name: str | None,
    database_name: str,
    schema_name: str,
    account_id: str,
) -> str | None:
    """Resolve a stream's source table reference to that table's node id.

    Snowflake reports the reference as plain dotted text, either bare or already
    database- and schema-qualified, and quotes only the components that need it. A
    component that itself contains a dot cannot be recovered from that text, so such
    a reference stays unresolved and the caller draws no edge rather than pointing
    one at the wrong table.
    """
    if not table_name:
        return None
    parts = [
        (
            part[1:-1]
            if len(part) > 1 and part.startswith('"') and part.endswith('"')
            else part
        )
        for part in table_name.split(".")
    ]
    if any(not part or '"' in part for part in parts):
        return None
    if len(parts) == 1:
        parts = [database_name, schema_name, parts[0]]
    elif len(parts) != 3:
        return None
    return sf_id(account_id, "table", sf_fqn(*parts))


@timeit
def get_schema_streams(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Streams of one schema, or None when the role cannot read that schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/streams",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list streams of Snowflake schema %s.%s (permission denied); they "
            "will be missing from the graph.",
            database_name,
            schema_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return one entry per readable schema, plus whether every schema was read.

    The stream payload does not repeat its database and schema, so each listing is
    returned alongside the parent it was fetched for.
    """
    listings: list[dict[str, Any]] = []
    complete = True
    for schema in schemas:
        database_name = schema["database_name"]
        schema_name = schema["name"]
        rows = get_schema_streams(client, database_name, schema_name)
        if rows is None:
            complete = False
            continue
        listings.append(
            {
                "database_name": database_name,
                "schema_name": schema_name,
                "streams": rows,
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
        for stream in listing["streams"]:
            name = stream["name"]
            qualified_name = sf_fqn(database_name, schema_name, name)
            source_name = _source_name(stream)
            source_type = _source_type(stream)
            transformed.append(
                {
                    "id": sf_id(account_id, "stream", qualified_name),
                    "name": name,
                    "qualified_name": qualified_name,
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "parent_schema_id": parent_schema_id,
                    # Snowflake has named this field both ways across API versions.
                    "source_type": source_type,
                    "source_name": source_name,
                    # Null when the source is not a table, or when its reference
                    # cannot be split, which suppresses the READS_FROM edge. A
                    # stream can also sit on a view or a stage, and those ids are
                    # type-tagged differently, so resolving them as a table would
                    # point the edge at an object that does not exist.
                    "source_table_id": (
                        _source_table_id(
                            source_name, database_name, schema_name, account_id
                        )
                        if str(source_type or "").lower() == "table"
                        else None
                    ),
                    "mode": stream.get("mode"),
                    "stream_type": stream.get("type"),
                    "is_stale": stream.get("stale"),
                    "stale_after": iso_to_datetime(stream.get("stale_after")),
                    "invalid_reason": stream.get("invalid_reason"),
                    "owner": stream.get("owner"),
                    "comment": stream.get("comment"),
                    "created_on": iso_to_datetime(stream.get("created_on")),
                },
            )
    return transformed


def load_streams(
    neo4j_session: neo4j.Session,
    streams: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeStreamSchema(),
        streams,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeStreamSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake streams, returning whether every schema could be read."""
    listings, complete = get(client, schemas)
    streams = transform(listings, client.account_id)
    logger.info(
        "Loading %d Snowflake streams for account %s.",
        len(streams),
        client.account_id,
    )
    load_streams(
        neo4j_session, streams, client.account_id, common_job_parameters["UPDATE_TAG"]
    )
    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be listed; skipping stream cleanup so "
            "still-valid streams are not deleted.",
        )
    return complete
