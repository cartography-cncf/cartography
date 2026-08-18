"""Snowflake notebooks: interactive code stored and executed inside the account."""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import external_access_integration_ids
from cartography.intel.snowflake.names import name_list
from cartography.intel.snowflake.names import secret_ids
from cartography.intel.snowflake.names import secret_references
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.notebook import SnowflakeNotebookSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Notebooks in one schema, or None when the schema is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/notebooks",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


def transform(
    notebooks: list[dict[str, Any]],
    schema: dict[str, Any],
    account_id: str,
) -> list[dict[str, Any]]:
    database_name = schema["database_name"]
    schema_name = schema["name"]
    transformed: list[dict[str, Any]] = []

    for notebook in notebooks:
        name = notebook["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        warehouse = notebook.get("query_warehouse")
        compute_pool = notebook.get("compute_pool")
        transformed.append(
            {
                "id": sf_id(account_id, "notebook", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": schema["id"],
                "title": notebook.get("title"),
                "query_warehouse": warehouse,
                "warehouse_id": (
                    sf_id(account_id, "warehouse", sf_fqn(warehouse))
                    if warehouse
                    else None
                ),
                "compute_pool": compute_pool,
                "compute_pool_id": (
                    sf_id(account_id, "compute_pool", sf_fqn(compute_pool))
                    if compute_pool
                    else None
                ),
                "external_access_integrations": name_list(
                    notebook.get("external_access_integrations"),
                ),
                "external_access_integration_ids": external_access_integration_ids(
                    notebook.get("external_access_integrations"),
                    account_id,
                ),
                "external_access_secrets": secret_references(
                    notebook.get("external_access_secrets"),
                ),
                "secret_ids": secret_ids(
                    notebook.get("external_access_secrets"),
                    database_name,
                    schema_name,
                    account_id,
                ),
                "runtime_name": notebook.get("runtime_name"),
                "default_version": notebook.get("default_version"),
                "main_file": notebook.get("main_file"),
                "url_id": notebook.get("url_id"),
                "import_urls": name_list(notebook.get("import_urls")),
                "live_version_location_uri": notebook.get("live_version_location_uri"),
                "owner": notebook.get("owner"),
                "comment": notebook.get("comment"),
                "created_on": iso_to_datetime(notebook.get("created_on")),
            },
        )
    return transformed


def load_notebooks(
    neo4j_session: neo4j.Session,
    notebooks: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeNotebookSchema(),
        notebooks,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeNotebookSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync every notebook in every readable schema.

    Returns whether the walk was complete, so the caller can skip notebook
    cleanup rather than deleting nodes it merely failed to re-read this run.
    """
    account_id = client.account_id
    notebooks: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        listing = get(client, schema["database_name"], schema["name"])
        if listing is None:
            complete = False
            continue
        notebooks.extend(transform(listing, schema, account_id))

    logger.info(
        "Loading %d Snowflake notebooks for account %s.",
        len(notebooks),
        account_id,
    )
    load_notebooks(
        neo4j_session, notebooks, account_id, common_job_parameters["UPDATE_TAG"]
    )

    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be read for notebooks; skipping "
            "notebook cleanup so still-valid nodes are not deleted.",
        )
    return complete
