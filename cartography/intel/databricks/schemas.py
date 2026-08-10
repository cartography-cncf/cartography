import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.schema import DatabricksSchemaSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    catalogs: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Sync UC schemas across all catalogs; returns them for table/volume sync."""
    schemas = get(api_session, catalogs)
    transformed = transform(schemas)
    load_schemas(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return schemas


@timeit
def get(
    api_session: DatabricksWorkspaceClient, catalogs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    for catalog in catalogs:
        catalog_name = catalog.get("name")
        if not catalog_name:
            continue
        try:
            schemas.extend(
                api_session.uc_list(
                    "/api/2.1/unity-catalog/schemas",
                    "schemas",
                    params={"catalog_name": catalog_name},
                )
            )
        except requests.HTTPError as e:
            # A 403 on a system-managed catalog (samples, system) is expected;
            # skip it. Any other error (transient 5xx, auth) must abort so the
            # caller does not run cleanup on partial data and delete valid nodes.
            skip_or_raise_http(e, 403)
            logger.warning(
                "Skipping schemas for catalog %s (permission denied): %s",
                catalog_name,
                e,
            )
    return schemas


@timeit
def transform(schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for s in schemas:
        metastore_id = s["metastore_id"]
        full_name = s["full_name"]
        if not full_name:
            raise ValueError("Databricks schema returned with empty full_name")
        result.append(
            {
                "id": uc_id(metastore_id, full_name),
                "schema_id": s.get("schema_id"),
                "name": s.get("name"),
                "full_name": full_name,
                "catalog_name": s.get("catalog_name"),
                "catalog_id": uc_id(metastore_id, s["catalog_name"]),
                "metastore_id": metastore_id,
                "owner": s.get("owner"),
                "comment": s.get("comment"),
                "storage_root": s.get("storage_root"),
                "created_at": epoch_ms_to_datetime(s.get("created_at")),
                "updated_at": epoch_ms_to_datetime(s.get("updated_at")),
                "created_by": s.get("created_by"),
                "updated_by": s.get("updated_by"),
            }
        )
    return result


@timeit
def load_schemas(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksSchemaSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksSchemaSchema(), common_job_parameters).run(
        neo4j_session
    )
