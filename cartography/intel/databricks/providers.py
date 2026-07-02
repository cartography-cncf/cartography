from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.provider import DatabricksProviderSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    metastore_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    providers = get(api_session)
    transformed = transform(providers, metastore_id)
    load_providers(
        neo4j_session, transformed, workspace_id, common_job_parameters["UPDATE_TAG"]
    )


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.uc_list("/api/2.1/unity-catalog/providers", "providers")


@timeit
def transform(
    providers: list[dict[str, Any]], metastore_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for p in providers:
        name = p["name"]
        if not name:
            raise ValueError("Databricks provider returned with empty name")
        result.append(
            {
                "id": uc_id(metastore_id, name),
                "name": name,
                "metastore_id": metastore_id,
                "authentication_type": p.get("authentication_type"),
                "owner": p.get("owner"),
                "comment": p.get("comment"),
                "data_provider_global_metastore_id": p.get(
                    "data_provider_global_metastore_id"
                ),
                "cloud": p.get("cloud"),
                "region": p.get("region"),
                "created_at": epoch_ms_to_datetime(p.get("created_at")),
                "created_by": p.get("created_by"),
                "updated_at": epoch_ms_to_datetime(p.get("updated_at")),
                "updated_by": p.get("updated_by"),
            }
        )
    return result


@timeit
def load_providers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksProviderSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksProviderSchema(), common_job_parameters).run(
        neo4j_session
    )
