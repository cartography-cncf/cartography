from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.models.databricks.metastore import DatabricksMetastoreSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> str | None:
    """Sync the metastore assigned to this workspace.

    Returns the metastore id so downstream UC syncs (catalogs, external
    locations, ...) can attach to it, or None when no metastore is assigned.
    """
    metastore = get(api_session)
    # Load empty + cleanup when the workspace has no metastore so a workspace
    # that lost its assignment does not leave a stale metastore node behind.
    transformed = transform(metastore) if metastore is not None else []
    load_metastores(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return metastore["metastore_id"] if metastore is not None else None


@timeit
def get(api_session: DatabricksWorkspaceClient) -> dict[str, Any] | None:
    """Fetch the workspace's metastore summary + assignment.

    A workspace without Unity Catalog enabled has no metastore assignment; the
    summary endpoint returns an empty body in that case.
    """
    summary = api_session.get("/api/2.1/unity-catalog/metastore_summary")
    if not summary.get("metastore_id"):
        return None
    assignment = api_session.get("/api/2.1/unity-catalog/current-metastore-assignment")
    return {**summary, "assignment": assignment or {}}


@timeit
def transform(metastore: dict[str, Any]) -> list[dict[str, Any]]:
    assignment = metastore.get("assignment") or {}
    return [
        {
            "id": metastore["metastore_id"],
            "metastore_id": metastore["metastore_id"],
            "name": metastore.get("name"),
            "global_metastore_id": metastore.get("global_metastore_id"),
            "cloud": metastore.get("cloud"),
            "region": metastore.get("region"),
            "delta_sharing_scope": metastore.get("delta_sharing_scope"),
            "external_access_enabled": metastore.get("external_access_enabled"),
            "privilege_model_version": metastore.get("privilege_model_version"),
            "owner": metastore.get("owner"),
            "storage_root": metastore.get("storage_root"),
            "created_at": epoch_ms_to_datetime(metastore.get("created_at")),
            "updated_at": epoch_ms_to_datetime(metastore.get("updated_at")),
            "default_catalog_name": assignment.get("default_catalog_name"),
            "workspace_numeric_id": assignment.get("workspace_id"),
        }
    ]


@timeit
def load_metastores(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksMetastoreSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksMetastoreSchema(), common_job_parameters).run(
        neo4j_session
    )
