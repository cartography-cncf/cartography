from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.repo import DatabricksRepoSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    repos = get(api_session)
    transformed = transform(repos, workspace_id)
    load_repos(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """Paginate repos (git folders) via ``repos`` + ``next_page_token``.

    ``path_prefix=/Workspace`` is required: called with no prefix the endpoint
    only returns repos under the legacy ``/Repos`` root and silently omits git
    folders under user home directories, so every workspace path is anchored
    under ``/Workspace``.
    """
    results: list[dict[str, Any]] = []
    base = {"path_prefix": "/Workspace"}
    params: dict[str, Any] = dict(base)
    seen_tokens: set[str] = set()
    while True:
        response = api_session.get("/api/2.0/repos", params=params)
        results.extend(response.get("repos", []) or [])
        next_token = response.get("next_page_token")
        if not next_token:
            break
        if next_token in seen_tokens:
            raise ValueError(
                f"Databricks repos list repeated page token {next_token!r}; "
                "aborting to avoid an infinite loop.",
            )
        seen_tokens.add(next_token)
        params = {**base, "next_page_token": next_token}
    return results


@timeit
def transform(repos: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for r in repos:
        repo_id = r.get("id")
        if not repo_id:
            raise ValueError("Databricks repo returned with empty id")
        result.append(
            {
                "id": scoped_id(workspace_id, str(repo_id)),
                "repo_id": str(repo_id),
                "url": r.get("url"),
                "provider": r.get("provider"),
                "branch": r.get("branch"),
                "head_commit_id": r.get("head_commit_id"),
                "path": r.get("path"),
            }
        )
    return result


@timeit
def load_repos(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksRepoSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksRepoSchema(), common_job_parameters).run(
        neo4j_session
    )
