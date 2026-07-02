from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.data_source import DatabricksDataSourceSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    data_sources = get(api_session)
    transformed = transform(data_sources, workspace_id)
    load_data_sources(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """List SQL data sources. The endpoint returns a bare list, no pagination."""
    response = api_session.get("/api/2.0/preview/sql/data_sources")
    if not isinstance(response, list):
        raise ValueError(
            "Databricks data sources endpoint returned "
            f"{type(response).__name__}, expected a list.",
        )
    return response


@timeit
def transform(
    data_sources: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for d in data_sources:
        data_source_id = d.get("id")
        if not data_source_id:
            raise ValueError("Databricks data source returned with empty id")
        warehouse_id = d.get("warehouse_id")
        result.append(
            {
                "id": scoped_id(workspace_id, data_source_id),
                "data_source_id": data_source_id,
                "name": d.get("name"),
                "type": d.get("type"),
                "warehouse_id": warehouse_id,
                "warehouse_scoped_id": (
                    scoped_id(workspace_id, warehouse_id) if warehouse_id else None
                ),
                "syntax": d.get("syntax"),
                # The API reports paused as 0/1; keep it as-is (0 == running).
                "paused": d.get("paused"),
                "view_only": d.get("view_only"),
            }
        )
    return result


@timeit
def load_data_sources(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksDataSourceSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksDataSourceSchema(), common_job_parameters).run(
        neo4j_session
    )
