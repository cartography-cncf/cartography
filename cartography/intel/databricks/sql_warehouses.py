from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.sql_warehouse import DatabricksSqlWarehouseSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    warehouses = get(api_session)
    transformed = transform(warehouses, workspace_id)
    load_warehouses(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """List SQL warehouses. The endpoint returns the full set in one response."""
    return api_session.get("/api/2.0/sql/warehouses").get("warehouses", []) or []


@timeit
def transform(
    warehouses: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for w in warehouses:
        warehouse_id = w["id"]
        if not warehouse_id:
            raise ValueError("Databricks SQL warehouse returned with empty id")
        result.append(
            {
                "id": scoped_id(workspace_id, warehouse_id),
                "warehouse_id": warehouse_id,
                "name": w.get("name"),
                "state": w.get("state"),
                "cluster_size": w.get("cluster_size"),
                "size": w.get("size"),
                "warehouse_type": w.get("warehouse_type"),
                "enable_serverless_compute": w.get("enable_serverless_compute"),
                "enable_photon": w.get("enable_photon"),
                "auto_stop_mins": w.get("auto_stop_mins"),
                "auto_resume": w.get("auto_resume"),
                "spot_instance_policy": w.get("spot_instance_policy"),
                "channel": (w.get("channel") or {}).get("name"),
                "min_num_clusters": w.get("min_num_clusters"),
                "max_num_clusters": w.get("max_num_clusters"),
                "num_clusters": w.get("num_clusters"),
                "creator_name": w.get("creator_name"),
                "jdbc_url": w.get("jdbc_url"),
            }
        )
    return result


@timeit
def load_warehouses(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksSqlWarehouseSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksSqlWarehouseSchema(), common_job_parameters
    ).run(neo4j_session)
