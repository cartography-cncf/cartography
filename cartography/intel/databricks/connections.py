from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.connection import DatabricksConnectionSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    connections = get(api_session)
    transformed = transform(connections)
    load_connections(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.uc_list("/api/2.1/unity-catalog/connections", "connections")


@timeit
def transform(connections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for c in connections:
        metastore_id = c["metastore_id"]
        name = c["name"]
        if not name:
            raise ValueError("Databricks connection returned with empty name")
        # `options` carries connection settings; keep host/port only (the rest
        # can hold secrets we deliberately do not ingest).
        options = c.get("options") or {}
        result.append(
            {
                "id": uc_id(metastore_id, name),
                "connection_id": c.get("connection_id"),
                "name": name,
                "full_name": c.get("full_name") or name,
                "metastore_id": metastore_id,
                "connection_type": c.get("connection_type"),
                "credential_type": c.get("credential_type"),
                "owner": c.get("owner"),
                "comment": c.get("comment"),
                "read_only": c.get("read_only"),
                "host": options.get("host") or options.get("hostname"),
                "port": options.get("port"),
                "created_at": epoch_ms_to_datetime(c.get("created_at")),
                "updated_at": epoch_ms_to_datetime(c.get("updated_at")),
                "created_by": c.get("created_by"),
                "updated_by": c.get("updated_by"),
            }
        )
    return result


@timeit
def load_connections(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksConnectionSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksConnectionSchema(), common_job_parameters).run(
        neo4j_session
    )
