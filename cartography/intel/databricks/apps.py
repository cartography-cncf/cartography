from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import iso_to_datetime
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.app import DatabricksAppSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    apps = get(api_session)
    transformed = transform(apps, workspace_id)
    load_apps(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """Paginate Databricks Apps via ``apps`` + ``next_page_token``."""
    results: list[dict[str, Any]] = []
    params: dict[str, Any] = {"page_size": 100}
    seen_tokens: set[str] = set()
    while True:
        response = api_session.get("/api/2.0/apps", params=params)
        results.extend(response.get("apps", []) or [])
        next_token = response.get("next_page_token")
        if not next_token:
            break
        if next_token in seen_tokens:
            raise ValueError(
                f"Databricks apps list repeated page token {next_token!r}; "
                "aborting to avoid an infinite loop.",
            )
        seen_tokens.add(next_token)
        params = {"page_size": 100, "page_token": next_token}
    return results


@timeit
def transform(apps: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for a in apps:
        name = a.get("name")
        if not name:
            raise ValueError("Databricks app returned with empty name")
        result.append(
            {
                "id": scoped_id(workspace_id, name),
                "name": name,
                "description": a.get("description"),
                "url": a.get("url"),
                "app_state": (a.get("app_status") or {}).get("state"),
                "compute_state": (a.get("compute_status") or {}).get("state"),
                "compute_size": a.get("compute_size"),
                "creator": a.get("creator"),
                "service_principal_client_id": a.get("service_principal_client_id"),
                "service_principal_name": a.get("service_principal_name"),
                "oauth2_app_client_id": a.get("oauth2_app_client_id"),
                "create_time": iso_to_datetime(a.get("create_time")),
                "update_time": iso_to_datetime(a.get("update_time")),
            }
        )
    return result


@timeit
def load_apps(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksAppSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksAppSchema(), common_job_parameters).run(
        neo4j_session
    )
