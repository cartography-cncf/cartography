from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.instance_pool import DatabricksInstancePoolSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    pools = get(api_session)
    transformed = transform(pools, workspace_id)
    load_instance_pools(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    response = api_session.get("/api/2.0/instance-pools/list")
    return response.get("instance_pools", []) or []


@timeit
def transform(pools: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for p in pools:
        # Fail loudly on missing/empty canonical id rather than minting a
        # corrupt `{workspace_id}/` node (team rule for Neo4j canonical ids).
        pool_id = p["instance_pool_id"]
        if not pool_id:
            raise ValueError(
                "Databricks instance pool returned with empty instance_pool_id"
            )
        result.append(
            {
                "id": scoped_id(workspace_id, pool_id),
                "instance_pool_id": pool_id,
                "instance_pool_name": p.get("instance_pool_name"),
                "node_type_id": p.get("node_type_id"),
                "min_idle_instances": p.get("min_idle_instances"),
                "max_capacity": p.get("max_capacity"),
                "idle_instance_autotermination_minutes": p.get(
                    "idle_instance_autotermination_minutes"
                ),
                "enable_elastic_disk": p.get("enable_elastic_disk"),
                "state": p.get("state"),
            }
        )
    return result


@timeit
def load_instance_pools(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksInstancePoolSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksInstancePoolSchema(), common_job_parameters
    ).run(neo4j_session)
