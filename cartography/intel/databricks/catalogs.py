from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.catalog import DatabricksCatalogSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Sync UC catalogs and return them so schemas can iterate per catalog."""
    catalogs = get(api_session)
    transformed = transform(catalogs)
    load_catalogs(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return catalogs


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.uc_list("/api/2.1/unity-catalog/catalogs", "catalogs")


@timeit
def transform(catalogs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for c in catalogs:
        metastore_id = c["metastore_id"]
        full_name = c["full_name"]
        if not full_name:
            raise ValueError("Databricks catalog returned with empty full_name")
        result.append(
            {
                "id": uc_id(metastore_id, full_name),
                "catalog_id": c.get("id"),
                "name": c.get("name"),
                "full_name": full_name,
                "metastore_id": metastore_id,
                "catalog_type": c.get("catalog_type"),
                "owner": c.get("owner"),
                "comment": c.get("comment"),
                "isolation_mode": c.get("isolation_mode"),
                "storage_root": c.get("storage_root"),
                "connection_name": c.get("connection_name"),
                "share_name": c.get("share_name"),
                "provider_name": c.get("provider_name"),
                "securable_kind": c.get("securable_kind"),
                "created_at": epoch_ms_to_datetime(c.get("created_at")),
                "updated_at": epoch_ms_to_datetime(c.get("updated_at")),
                "created_by": c.get("created_by"),
                "updated_by": c.get("updated_by"),
            }
        )
    return result


@timeit
def load_catalogs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksCatalogSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksCatalogSchema(), common_job_parameters).run(
        neo4j_session
    )
