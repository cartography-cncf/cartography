import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import iso_to_datetime
from cartography.intel.databricks.util import scoped_id
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.models.databricks.dashboard import DatabricksDashboardSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    dashboards = get_lakeview(api_session) + get_legacy(api_session)
    transformed = transform(dashboards, workspace_id)
    load_dashboards(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_lakeview(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """Paginate current (Lakeview) dashboards."""
    results: list[dict[str, Any]] = []
    params: dict[str, Any] = {"page_size": 100}
    while True:
        response = api_session.get("/api/2.0/lakeview/dashboards", params=params)
        for d in response.get("dashboards", []) or []:
            results.append({**d, "_type": "LAKEVIEW"})
        next_token = response.get("next_page_token")
        if not next_token:
            break
        params = {"page_size": 100, "page_token": next_token}
    return results


@timeit
def get_legacy(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """Paginate legacy (redash-based) dashboards.

    The legacy ``/preview/sql/dashboards`` surface is deprecated and absent in
    some workspaces; a 404/400 there is skippable so it never aborts the sync.
    """
    results: list[dict[str, Any]] = []
    page = 1
    while True:
        try:
            response = api_session.get(
                "/api/2.0/preview/sql/dashboards",
                params={"page_size": 100, "page": page},
            )
        except requests.HTTPError as e:
            skip_or_raise_http(e, 400, 404)
            logger.info("Legacy SQL dashboards API unavailable, skipping: %s", e)
            break
        batch = response.get("results", []) or []
        for d in batch:
            results.append({**d, "_type": "LEGACY"})
        count = int(response.get("count", 0))
        if not batch or len(results) >= count:
            break
        page += 1
    return results


@timeit
def transform(
    dashboards: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for d in dashboards:
        dashboard_type = d["_type"]
        dashboard_id = d.get("dashboard_id") or d.get("id")
        if not dashboard_id:
            raise ValueError("Databricks dashboard returned with empty id")
        warehouse_id = d.get("warehouse_id")
        # Lakeview carries display_name + RFC-3339 timestamps; legacy carries
        # name + a nested user object and created_at/updated_at.
        result.append(
            {
                "id": scoped_id(workspace_id, dashboard_id),
                "dashboard_id": dashboard_id,
                "dashboard_type": dashboard_type,
                "display_name": d.get("display_name") or d.get("name"),
                "warehouse_id": warehouse_id,
                "warehouse_scoped_id": (
                    scoped_id(workspace_id, warehouse_id) if warehouse_id else None
                ),
                "owner_user_name": (d.get("user") or {}).get("email"),
                "lifecycle_state": d.get("lifecycle_state"),
                "parent_path": d.get("parent_path"),
                "path": d.get("path"),
                "create_time": iso_to_datetime(
                    d.get("create_time") or d.get("created_at")
                ),
                "update_time": iso_to_datetime(
                    d.get("update_time") or d.get("updated_at")
                ),
            }
        )
    return result


@timeit
def load_dashboards(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksDashboardSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksDashboardSchema(), common_job_parameters).run(
        neo4j_session
    )
