from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.genie_space import DatabricksGenieSpaceSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    spaces = get(api_session)
    transformed = transform(spaces, workspace_id)
    load_genie_spaces(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """Paginate Genie spaces (``spaces`` + ``next_page_token``)."""
    results: list[dict[str, Any]] = []
    params: dict[str, Any] = {"page_size": 100}
    seen_tokens: set[str] = set()
    while True:
        response = api_session.get("/api/2.0/genie/spaces", params=params)
        results.extend(response.get("spaces", []) or [])
        next_token = response.get("next_page_token")
        if not next_token:
            break
        if next_token in seen_tokens:
            raise ValueError(
                f"Databricks Genie spaces list repeated page token "
                f"{next_token!r}; aborting to avoid an infinite loop.",
            )
        seen_tokens.add(next_token)
        params = {"page_size": 100, "page_token": next_token}
    return results


@timeit
def transform(spaces: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for s in spaces:
        space_id = s.get("space_id")
        if not space_id:
            raise ValueError("Databricks Genie space returned with empty space_id")
        warehouse_id = s.get("warehouse_id")
        result.append(
            {
                "id": scoped_id(workspace_id, space_id),
                "space_id": space_id,
                "title": s.get("title"),
                "description": s.get("description"),
                "warehouse_id": warehouse_id,
                "warehouse_scoped_id": (
                    scoped_id(workspace_id, warehouse_id) if warehouse_id else None
                ),
            }
        )
    return result


@timeit
def load_genie_spaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksGenieSpaceSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksGenieSpaceSchema(), common_job_parameters).run(
        neo4j_session
    )
