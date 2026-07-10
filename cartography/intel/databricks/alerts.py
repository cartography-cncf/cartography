from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import iso_to_datetime
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.alert import DatabricksAlertSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    alerts = get(api_session)
    transformed = transform(alerts, workspace_id)
    load_alerts(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """Paginate the SQL alerts listing (``results`` + ``next_page_token``)."""
    results: list[dict[str, Any]] = []
    params: dict[str, Any] = {"page_size": 100}
    while True:
        response = api_session.get("/api/2.0/sql/alerts", params=params)
        results.extend(response.get("results", []) or [])
        next_token = response.get("next_page_token")
        if not next_token:
            break
        params = {"page_size": 100, "page_token": next_token}
    return results


@timeit
def transform(alerts: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for a in alerts:
        alert_id = a.get("id")
        if not alert_id:
            raise ValueError("Databricks alert returned with empty id")
        query_id = a.get("query_id")
        result.append(
            {
                "id": scoped_id(workspace_id, alert_id),
                "alert_id": alert_id,
                "display_name": a.get("display_name"),
                "query_id": query_id,
                "query_scoped_id": (
                    scoped_id(workspace_id, query_id) if query_id else None
                ),
                "owner_user_name": a.get("owner_user_name"),
                "state": a.get("state"),
                "lifecycle_state": a.get("lifecycle_state"),
                "condition_op": (a.get("condition") or {}).get("op"),
                "parent_path": a.get("parent_path"),
                "create_time": iso_to_datetime(a.get("create_time")),
                "update_time": iso_to_datetime(a.get("update_time")),
            }
        )
    return result


@timeit
def load_alerts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksAlertSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksAlertSchema(), common_job_parameters).run(
        neo4j_session
    )
