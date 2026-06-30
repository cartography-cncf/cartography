from datetime import datetime
from datetime import timezone
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.cluster_policy import DatabricksClusterPolicySchema
from cartography.util import timeit


def _epoch_ms_to_datetime(value: Any) -> datetime | None:
    if value in (None, 0):
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    policies = get(api_session)
    transformed = transform(policies, workspace_id)
    load_cluster_policies(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    response = api_session.get("/api/2.0/policies/clusters/list")
    return response.get("policies", []) or []


@timeit
def transform(
    policies: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    """Scope ids to the workspace; policy ids are workspace-local."""
    result: list[dict[str, Any]] = []
    for p in policies:
        # Fail loudly on missing/empty canonical id rather than minting a
        # corrupt `{workspace_id}/` node (team rule for Neo4j canonical ids).
        policy_id = p["policy_id"]
        if not policy_id:
            raise ValueError("Databricks cluster policy returned with empty policy_id")
        result.append(
            {
                "id": scoped_id(workspace_id, policy_id),
                "policy_id": policy_id,
                "name": p.get("name"),
                "description": p.get("description"),
                "definition": p.get("definition"),
                "policy_family_id": p.get("policy_family_id"),
                "creator_user_name": p.get("creator_user_name"),
                "created_at": _epoch_ms_to_datetime(p.get("created_at_timestamp")),
            }
        )
    return result


@timeit
def load_cluster_policies(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksClusterPolicySchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksClusterPolicySchema(), common_job_parameters
    ).run(neo4j_session)
