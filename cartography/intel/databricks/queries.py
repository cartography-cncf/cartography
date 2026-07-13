from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import iso_to_datetime
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.query import DatabricksQuerySchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    queries = get(api_session)
    transformed = transform(queries, workspace_id)
    load_queries(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """Paginate the SQL queries listing (``results`` + ``next_page_token``)."""
    results: list[dict[str, Any]] = []
    params: dict[str, Any] = {"page_size": 100}
    while True:
        response = api_session.get("/api/2.0/sql/queries", params=params)
        results.extend(response.get("results", []) or [])
        next_token = response.get("next_page_token")
        if not next_token:
            break
        params = {"page_size": 100, "page_token": next_token}
    return results


@timeit
def transform(queries: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for q in queries:
        query_id = q.get("id")
        if not query_id:
            raise ValueError("Databricks query returned with empty id")
        warehouse_id = q.get("warehouse_id")
        result.append(
            {
                "id": scoped_id(workspace_id, query_id),
                "query_id": query_id,
                "display_name": q.get("display_name"),
                "warehouse_id": warehouse_id,
                "warehouse_scoped_id": (
                    scoped_id(workspace_id, warehouse_id) if warehouse_id else None
                ),
                "query_text": q.get("query_text"),
                "owner_user_name": q.get("owner_user_name"),
                "last_modifier_user_name": q.get("last_modifier_user_name"),
                "run_as_mode": q.get("run_as_mode"),
                "lifecycle_state": q.get("lifecycle_state"),
                "parent_path": q.get("parent_path"),
                "create_time": iso_to_datetime(q.get("create_time")),
                "update_time": iso_to_datetime(q.get("update_time")),
            }
        )
    return result


@timeit
def load_queries(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksQuerySchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksQuerySchema(), common_job_parameters).run(
        neo4j_session
    )
