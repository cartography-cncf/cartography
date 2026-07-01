import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import parse_storage_url
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.table import DatabricksTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    tables = get(api_session, schemas)
    transformed = transform(tables)
    load_tables(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )


@timeit
def get(
    api_session: DatabricksWorkspaceClient, schemas: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for s in schemas:
        catalog_name = s.get("catalog_name")
        schema_name = s.get("name")
        if not catalog_name or not schema_name:
            continue
        try:
            tables.extend(
                api_session.uc_list(
                    "/api/2.1/unity-catalog/tables",
                    "tables",
                    params={
                        "catalog_name": catalog_name,
                        "schema_name": schema_name,
                    },
                )
            )
        except requests.HTTPError as e:
            # Skip an expected 403 on a system-managed schema; re-raise anything
            # else so cleanup does not run on partial data.
            skip_or_raise_http(e, 403)
            logger.warning(
                "Skipping tables for schema %s.%s (permission denied): %s",
                catalog_name,
                schema_name,
                e,
            )
    return tables


@timeit
def transform(tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for t in tables:
        metastore_id = t["metastore_id"]
        full_name = t["full_name"]
        if not full_name:
            raise ValueError("Databricks table returned with empty full_name")
        parent_schema = f"{t['catalog_name']}.{t['schema_name']}"
        scheme, bucket = parse_storage_url(t.get("storage_location"))
        result.append(
            {
                "id": uc_id(metastore_id, full_name),
                "table_id": t.get("table_id"),
                "name": t.get("name"),
                "full_name": full_name,
                "catalog_name": t.get("catalog_name"),
                "schema_name": t.get("schema_name"),
                "parent_schema_id": uc_id(metastore_id, parent_schema),
                "metastore_id": metastore_id,
                "table_type": t.get("table_type"),
                "data_source_format": t.get("data_source_format"),
                "owner": t.get("owner"),
                "comment": t.get("comment"),
                "storage_location": t.get("storage_location"),
                "view_definition": t.get("view_definition"),
                "created_at": epoch_ms_to_datetime(t.get("created_at")),
                "updated_at": epoch_ms_to_datetime(t.get("updated_at")),
                "created_by": t.get("created_by"),
                "updated_by": t.get("updated_by"),
                "s3_bucket": bucket if scheme in ("s3", "s3a") else None,
                "gcs_bucket": bucket if scheme == "gs" else None,
            }
        )
    return result


@timeit
def load_tables(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksTableSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksTableSchema(), common_job_parameters).run(
        neo4j_session
    )
