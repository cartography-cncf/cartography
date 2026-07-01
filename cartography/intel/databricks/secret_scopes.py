from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.secret_scope import DatabricksSecretScopeSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    scopes = get(api_session)
    transformed = transform(scopes, workspace_id)
    load_secret_scopes(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    response = api_session.get("/api/2.0/secrets/scopes/list")
    return response.get("scopes", []) or []


@timeit
def transform(scopes: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    """Flatten ``keyvault_metadata`` so Azure KV-backed scopes carry resource id + DNS."""
    result: list[dict[str, Any]] = []
    for s in scopes:
        # Fail loudly on missing/empty canonical id rather than minting a
        # corrupt `{workspace_id}/` node (team rule for Neo4j canonical ids).
        name = s["name"]
        if not name:
            raise ValueError("Databricks secret scope returned with empty name")
        keyvault = s.get("keyvault_metadata") or {}
        result.append(
            {
                "id": scoped_id(workspace_id, name),
                "name": name,
                "backend_type": s.get("backend_type"),
                "keyvault_resource_id": keyvault.get("resource_id"),
                "keyvault_dns_name": keyvault.get("dns_name"),
            }
        )
    return result


@timeit
def load_secret_scopes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksSecretScopeSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksSecretScopeSchema(), common_job_parameters).run(
        neo4j_session
    )
