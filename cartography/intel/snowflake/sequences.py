"""Snowflake sequences, the generators behind surrogate keys.

Sequences carry no data of their own, but a role that can read one can infer how many
rows an application has created, and a role that can alter one can break every table
that defaults from it.
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
from cartography.models.snowflake.sequence import SnowflakeSequenceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_schema_sequences(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Sequences of one schema, or None when the role cannot read that schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/sequences",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list sequences of Snowflake schema %s.%s (permission denied); "
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

    The sequence payload does not repeat its database and schema, so each listing is
    returned alongside the parent it was fetched for.
    """
    listings: list[dict[str, Any]] = []
    complete = True
    for schema in schemas:
        database_name = schema["database_name"]
        schema_name = schema["name"]
        rows = get_schema_sequences(client, database_name, schema_name)
        if rows is None:
            complete = False
            continue
        listings.append(
            {
                "database_name": database_name,
                "schema_name": schema_name,
                "sequences": rows,
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
        for sequence in listing["sequences"]:
            name = sequence["name"]
            qualified_name = sf_fqn(database_name, schema_name, name)
            transformed.append(
                {
                    "id": sf_id(account_id, "sequence", qualified_name),
                    "name": name,
                    "qualified_name": qualified_name,
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "parent_schema_id": parent_schema_id,
                    "start_value": sequence.get("start_value"),
                    "increment": sequence.get("increment"),
                    "next_value": sequence.get("next_value"),
                    "owner": sequence.get("owner"),
                    "comment": sequence.get("comment"),
                    "created_on": iso_to_datetime(sequence.get("created_on")),
                },
            )
    return transformed


def load_sequences(
    neo4j_session: neo4j.Session,
    sequences: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeSequenceSchema(),
        sequences,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeSequenceSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake sequences, returning whether every schema could be read."""
    listings, complete = get(client, schemas)
    sequences = transform(listings, client.account_id)
    logger.info(
        "Loading %d Snowflake sequences for account %s.",
        len(sequences),
        client.account_id,
    )
    load_sequences(
        neo4j_session, sequences, client.account_id, common_job_parameters["UPDATE_TAG"]
    )
    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be listed; skipping sequence cleanup "
            "so still-valid sequences are not deleted.",
        )
    return complete
