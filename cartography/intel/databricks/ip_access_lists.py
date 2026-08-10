import logging
from datetime import datetime
from datetime import timezone
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.ip_access_list import DatabricksIpAccessListSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


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
    access_lists = get(api_session)
    transformed = transform(access_lists, workspace_id)
    load_ip_access_lists(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """List workspace IP access lists.

    Standard-tier workspaces return HTTP 404 with ``error_code=FEATURE_DISABLED``
    because IP access lists are an enterprise-tier feature; treat that as
    "no lists configured" so the sync stays usable on those workspaces.
    """
    try:
        response = api_session.get("/api/2.0/ip-access-lists")
    except requests.HTTPError as exc:
        if (
            exc.response is not None
            and exc.response.status_code == 404
            and exc.response.json().get("error_code") == "FEATURE_DISABLED"
        ):
            logger.info(
                "Databricks IP access lists are not available on this workspace's pricing tier; skipping."
            )
            return []
        raise
    return response.get("ip_access_lists", []) or []


@timeit
def transform(
    access_lists: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for a in access_lists:
        # Fail loudly on missing/empty canonical id rather than minting a
        # corrupt `{workspace_id}/` node (team rule for Neo4j canonical ids).
        list_id = a["list_id"]
        if not list_id:
            raise ValueError("Databricks IP access list returned with empty list_id")
        result.append(
            {
                "id": scoped_id(workspace_id, list_id),
                "list_id": list_id,
                "label": a.get("label"),
                "list_type": a.get("list_type"),
                "enabled": a.get("enabled"),
                "address_count": a.get("address_count"),
                "ip_addresses": a.get("ip_addresses") or [],
                "created_at": _epoch_ms_to_datetime(a.get("created_at")),
                "updated_at": _epoch_ms_to_datetime(a.get("updated_at")),
            }
        )
    return result


@timeit
def load_ip_access_lists(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksIpAccessListSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksIpAccessListSchema(), common_job_parameters
    ).run(neo4j_session)
