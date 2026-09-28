"""Snowflake tag definitions: the governance keys objects and columns can carry."""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import name_list
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.tag import SnowflakeTagSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Tag definitions in one schema, or None when the schema is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/tags",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


def transform(
    tags: list[dict[str, Any]],
    schema: dict[str, Any],
    account_id: str,
) -> list[dict[str, Any]]:
    database_name = schema["database_name"]
    schema_name = schema["name"]
    transformed: list[dict[str, Any]] = []

    for tag in tags:
        name = tag["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        transformed.append(
            {
                "id": sf_id(account_id, "tag", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": schema["id"],
                "allowed_values": name_list(tag.get("allowed_values")),
                "owner": tag.get("owner"),
                "comment": tag.get("comment"),
                "created_on": iso_to_datetime(tag.get("created_on")),
            },
        )
    return transformed


def load_tags(
    neo4j_session: neo4j.Session,
    tags: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeTagSchema(),
        tags,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeTagSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync every tag definition in every readable schema.

    Returns whether the walk was complete, so the caller can skip tag cleanup
    rather than deleting nodes it merely failed to re-read this run.
    """
    account_id = client.account_id
    tags: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        listing = get(client, schema["database_name"], schema["name"])
        if listing is None:
            complete = False
            continue
        tags.extend(transform(listing, schema, account_id))

    logger.info(
        "Loading %d Snowflake tag definitions for account %s.",
        len(tags),
        account_id,
    )
    load_tags(neo4j_session, tags, account_id, common_job_parameters["UPDATE_TAG"])

    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be read for tags; skipping tag "
            "cleanup so still-valid nodes are not deleted.",
        )
    return complete
