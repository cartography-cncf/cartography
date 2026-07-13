from datetime import datetime
from datetime import timezone
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.cluster import DatabricksClusterSchema
from cartography.util import timeit


def _epoch_ms_to_datetime(value: Any) -> datetime | None:
    if value in (None, 0):
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)


def _scoped_or_none(workspace_id: str, value: Any) -> str | None:
    if value in (None, ""):
        return None
    return scoped_id(workspace_id, str(value))


def _pool_ids_scoped(workspace_id: str, cluster: dict[str, Any]) -> list[str]:
    """Dedupe worker + driver pool ids and scope to the workspace.

    Clusters may target a separate ``driver_instance_pool_id`` from their
    worker ``instance_pool_id``; both belong on the cluster's
    USES_INSTANCE_POOL edge so blast-radius queries see the full set.
    """
    scoped: list[str] = []
    for key in ("instance_pool_id", "driver_instance_pool_id"):
        s = _scoped_or_none(workspace_id, cluster.get(key))
        if s is not None and s not in scoped:
            scoped.append(s)
    return scoped


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    clusters = get(api_session)
    transformed = transform(clusters, workspace_id)
    load_clusters(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """List clusters via the 2.1 endpoint (handles pagination via page_token)."""
    results: list[dict[str, Any]] = []
    params: dict[str, Any] = {"page_size": 100}
    while True:
        response = api_session.get("/api/2.1/clusters/list", params=params)
        results.extend(response.get("clusters", []) or [])
        next_token = response.get("next_page_token")
        if not next_token:
            break
        params = {"page_size": 100, "page_token": next_token}
    return results


@timeit
def transform(
    clusters: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    """Scope ids to the workspace and resolve foreign-key edges.

    ``policy_id_scoped`` / ``instance_pool_id_scoped`` are the workspace-scoped
    composite ids matched against the policy/pool nodes, mirroring the
    composite-id convention used for users, tokens, etc.
    """
    result: list[dict[str, Any]] = []
    for c in clusters:
        # Fail loudly on missing/empty canonical id rather than minting a
        # corrupt `{workspace_id}/` node (team rule for Neo4j canonical ids).
        cluster_id = c["cluster_id"]
        if not cluster_id:
            raise ValueError("Databricks cluster returned with empty cluster_id")
        result.append(
            {
                "id": scoped_id(workspace_id, cluster_id),
                "cluster_id": cluster_id,
                "cluster_name": c.get("cluster_name"),
                "state": c.get("state"),
                "spark_version": c.get("spark_version"),
                "runtime_engine": c.get("runtime_engine"),
                "node_type_id": c.get("node_type_id"),
                "driver_node_type_id": c.get("driver_node_type_id"),
                "num_workers": c.get("num_workers"),
                "autotermination_minutes": c.get("autotermination_minutes"),
                "cluster_source": c.get("cluster_source"),
                "data_security_mode": c.get("data_security_mode"),
                "single_user_name": c.get("single_user_name"),
                "creator_user_name": c.get("creator_user_name"),
                "instance_pool_id": c.get("instance_pool_id"),
                "driver_instance_pool_id": c.get("driver_instance_pool_id"),
                "enable_local_disk_encryption": c.get("enable_local_disk_encryption"),
                "enable_elastic_disk": c.get("enable_elastic_disk"),
                "start_time": _epoch_ms_to_datetime(c.get("start_time")),
                "terminated_time": _epoch_ms_to_datetime(c.get("terminated_time")),
                "policy_id_scoped": _scoped_or_none(workspace_id, c.get("policy_id")),
                "instance_pool_ids_scoped": _pool_ids_scoped(workspace_id, c),
            }
        )
    return result


@timeit
def load_clusters(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksClusterSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksClusterSchema(), common_job_parameters).run(
        neo4j_session
    )
