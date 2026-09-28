"""Snowflake views, listed per schema.

A view's ``secure`` flag is the security-relevant part: a non-secure view leaks its
definition to anyone who can see the object and lets the optimizer expose rows the
definition was written to filter out, so a view used as an access boundary has to be
secure.
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
from cartography.models.snowflake.view import SnowflakeViewSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_schema_views(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Views of one schema, or None when the role cannot read that schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/views",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list views of Snowflake schema %s.%s (permission denied); they "
            "will be missing from the graph.",
            database_name,
            schema_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return every readable view plus whether every schema could be read."""
    views: list[dict[str, Any]] = []
    complete = True
    for schema in schemas:
        rows = get_schema_views(client, schema["database_name"], schema["name"])
        if rows is None:
            complete = False
            continue
        views.extend(rows)
    return views, complete


def transform(views: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for view in views:
        database_name = view["database_name"]
        schema_name = view["schema_name"]
        name = view["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        columns = view.get("columns")
        transformed.append(
            {
                "id": sf_id(account_id, "view", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                "kind": view.get("kind"),
                "is_secure": view.get("secure"),
                "query": view.get("query"),
                "column_count": len(columns) if columns is not None else None,
                "owner": view.get("owner"),
                "owner_role_type": view.get("owner_role_type"),
                "comment": view.get("comment"),
                "created_on": iso_to_datetime(view.get("created_on")),
            },
        )
    return transformed


def load_views(
    neo4j_session: neo4j.Session,
    views: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeViewSchema(),
        views,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeViewSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake views, returning whether every schema could be read."""
    raw_views, complete = get(client, schemas)
    views = transform(raw_views, client.account_id)
    logger.info(
        "Loading %d Snowflake views for account %s.", len(views), client.account_id
    )
    load_views(
        neo4j_session, views, client.account_id, common_job_parameters["UPDATE_TAG"]
    )
    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be listed; skipping view cleanup so "
            "still-valid views are not deleted.",
        )
    return complete
