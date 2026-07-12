from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.git_credential import DatabricksGitCredentialSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    credentials = get(api_session)
    transformed = transform(credentials, workspace_id)
    load_git_credentials(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """List Git credentials. The endpoint returns the full set in one response."""
    return api_session.get("/api/2.0/git-credentials").get("credentials", []) or []


@timeit
def transform(
    credentials: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for c in credentials:
        credential_id = c.get("credential_id")
        if not credential_id:
            raise ValueError("Databricks git credential returned with empty id")
        result.append(
            {
                "id": scoped_id(workspace_id, str(credential_id)),
                "credential_id": str(credential_id),
                "git_provider": c.get("git_provider"),
                "git_username": c.get("git_username"),
            }
        )
    return result


@timeit
def load_git_credentials(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksGitCredentialSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksGitCredentialSchema(), common_job_parameters
    ).run(neo4j_session)
