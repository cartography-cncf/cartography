"""Snowflake stages: the file locations data is loaded from and unloaded to.

Stages are listed per schema. An external stage carries a cloud storage ``url``, which
is parsed into the bucket or storage account so the stage links to the S3 / GCS / Azure
resource the aws, gcp and azure modules already ingested. An internal stage has no url
and lives in Snowflake-managed storage instead.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import parse_stage_url
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.stage import SnowflakeStageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_schema_stages(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Stages of one schema, or None when the role cannot read that schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/stages",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list stages of Snowflake schema %s.%s (permission denied); they "
            "will be missing from the graph.",
            database_name,
            schema_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return every readable stage plus whether every schema could be read.

    Unlike most schema-scoped endpoints, the stage listing does not repeat the
    stage's ``database_name`` / ``schema_name``, so the parent is attached here from
    the schema being walked. Taking it from the walked schema rather than the
    payload also guarantees the recomputed ``parent_schema_id`` matches the schema
    node's own id exactly.
    """
    stages: list[dict[str, Any]] = []
    complete = True
    for schema in schemas:
        rows = get_schema_stages(client, schema["database_name"], schema["name"])
        if rows is None:
            complete = False
            continue
        for row in rows:
            stages.append(
                {
                    **row,
                    "database_name": schema["database_name"],
                    "schema_name": schema["name"],
                },
            )
    return stages, complete


def _directory_table_enabled(directory_table: Any) -> bool | None:
    """Reduce the stage's directory-table settings to whether one is enabled.

    Snowflake returns a nested object here (``enable``, ``auto_refresh``,
    ``aws_sns_topic``, ...). Neo4j properties must be primitives, so only the
    enablement flag is kept; the refresh plumbing is not security-relevant.
    """
    if isinstance(directory_table, dict):
        return bool(directory_table.get("enable"))
    if directory_table is None:
        return None
    return bool(directory_table)


def transform(stages: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for stage in stages:
        database_name = stage["database_name"]
        schema_name = stage["schema_name"]
        name = stage["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        url = stage.get("url") or None
        scheme, container = parse_stage_url(url)
        storage_integration = stage.get("storage_integration") or None
        transformed.append(
            {
                "id": sf_id(account_id, "stage", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                "kind": stage.get("kind"),
                # A string, not a boolean: the conditional ObjectStorage and
                # FileStorage labels match on an exact string value.
                "is_external": "true" if url else "false",
                "url": url,
                "endpoint": stage.get("endpoint"),
                "storage_integration": storage_integration,
                # Null when the stage embeds its own credentials instead, which
                # suppresses the edge rather than pointing it at a nonexistent node.
                "storage_integration_id": (
                    sf_id(
                        account_id,
                        "storage_integration",
                        sf_fqn(storage_integration),
                    )
                    if storage_integration
                    else None
                ),
                "cloud": stage.get("cloud"),
                "region": stage.get("region"),
                "has_credentials": stage.get("has_credentials"),
                "has_encryption_key": stage.get("has_encryption_key"),
                "directory_table": _directory_table_enabled(
                    stage.get("directory_table")
                ),
                "owner": stage.get("owner"),
                "owner_role_type": stage.get("owner_role_type"),
                "comment": stage.get("comment"),
                "created_on": iso_to_datetime(stage.get("created_on")),
                "s3_bucket": container if scheme in ("s3", "s3gov") else None,
                "gcs_bucket": container if scheme == "gcs" else None,
                "azure_storage_account": (
                    container if scheme in ("azure", "azures") else None
                ),
            },
        )
    return transformed


def load_stages(
    neo4j_session: neo4j.Session,
    stages: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeStageSchema(),
        stages,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeStageSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake stages, returning whether every schema could be read.

    Runs after storage integrations so the USES_INTEGRATION edge resolves on the first
    pass.
    """
    raw_stages, complete = get(client, schemas)
    stages = transform(raw_stages, client.account_id)
    logger.info(
        "Loading %d Snowflake stages for account %s.", len(stages), client.account_id
    )
    load_stages(
        neo4j_session, stages, client.account_id, common_job_parameters["UPDATE_TAG"]
    )
    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be listed; skipping stage cleanup so "
            "still-valid stages are not deleted.",
        )
    return complete
