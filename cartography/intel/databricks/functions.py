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
from cartography.models.databricks.function import DatabricksFunctionSchema
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
    functions = get(api_session, schemas)
    transformed = transform(functions)
    load_functions(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )


@timeit
def get(
    api_session: DatabricksWorkspaceClient, schemas: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    functions: list[dict[str, Any]] = []
    for s in schemas:
        catalog_name = s.get("catalog_name")
        schema_name = s.get("name")
        if not catalog_name or not schema_name:
            continue
        try:
            functions.extend(
                api_session.uc_list(
                    "/api/2.1/unity-catalog/functions",
                    "functions",
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
                "Skipping functions for schema %s.%s (permission denied): %s",
                catalog_name,
                schema_name,
                e,
            )
    return functions


@timeit
def transform(functions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for f in functions:
        metastore_id = f["metastore_id"]
        full_name = f["full_name"]
        if not full_name:
            raise ValueError("Databricks function returned with empty full_name")
        parent_schema = f"{f['catalog_name']}.{f['schema_name']}"
        result.append(
            {
                "id": uc_id(metastore_id, full_name),
                "function_id": f.get("function_id"),
                "name": f.get("name"),
                "full_name": full_name,
                "catalog_name": f.get("catalog_name"),
                "schema_name": f.get("schema_name"),
                "parent_schema_id": uc_id(metastore_id, parent_schema),
                "metastore_id": metastore_id,
                "data_type": f.get("data_type"),
                "routine_body": f.get("routine_body"),
                "external_language": f.get("external_language"),
                "security_type": f.get("security_type"),
                "sql_data_access": f.get("sql_data_access"),
                "is_deterministic": f.get("is_deterministic"),
                "owner": f.get("owner"),
                "comment": f.get("comment"),
                "created_at": epoch_ms_to_datetime(f.get("created_at")),
                "updated_at": epoch_ms_to_datetime(f.get("updated_at")),
                "created_by": f.get("created_by"),
                "updated_by": f.get("updated_by"),
            }
        )
    return result


@timeit
def load_functions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksFunctionSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksFunctionSchema(), common_job_parameters).run(
        neo4j_session
    )
