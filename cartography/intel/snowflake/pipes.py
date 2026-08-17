"""Snowflake pipes: continuous loads from cloud storage into tables."""

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
from cartography.models.snowflake.pipe import SnowflakePipeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Pipes in one schema, or None when the schema is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/pipes",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


def transform(
    pipes: list[dict[str, Any]],
    schema: dict[str, Any],
    account_id: str,
) -> list[dict[str, Any]]:
    database_name = schema["database_name"]
    schema_name = schema["name"]
    transformed: list[dict[str, Any]] = []

    for pipe in pipes:
        name = pipe["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        integration = pipe.get("integration")
        transformed.append(
            {
                "id": sf_id(account_id, "pipe", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": schema["id"],
                # Snowflake reports the COPY statement under both names depending
                # on the endpoint version; either one is the pipe's definition.
                "definition": pipe.get("definition") or pipe.get("copy_statement"),
                "pattern": pipe.get("pattern"),
                "integration": integration,
                "integration_id": (
                    sf_id(account_id, "notification_integration", sf_fqn(integration))
                    if integration
                    else None
                ),
                "auto_ingest": pipe.get("auto_ingest"),
                "aws_sns_topic": pipe.get("aws_sns_topic"),
                "error_integration": pipe.get("error_integration"),
                "invalid_reason": pipe.get("invalid_reason"),
                "owner": pipe.get("owner"),
                "comment": pipe.get("comment"),
                "created_on": iso_to_datetime(pipe.get("created_on")),
            },
        )
    return transformed


def load_pipes(
    neo4j_session: neo4j.Session,
    pipes: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakePipeSchema(),
        pipes,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakePipeSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync every pipe in every readable schema.

    Returns whether the walk was complete, so the caller can skip pipe cleanup
    rather than deleting nodes it merely failed to re-read this run.
    """
    account_id = client.account_id
    pipes: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        listing = get(client, schema["database_name"], schema["name"])
        if listing is None:
            complete = False
            continue
        pipes.extend(transform(listing, schema, account_id))

    logger.info(
        "Loading %d Snowflake pipes for account %s.",
        len(pipes),
        account_id,
    )
    load_pipes(neo4j_session, pipes, account_id, common_job_parameters["UPDATE_TAG"])

    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be read for pipes; skipping pipe "
            "cleanup so still-valid nodes are not deleted.",
        )
    return complete
