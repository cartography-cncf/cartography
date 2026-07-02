import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import scoped_id
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.models.databricks.clean_room import DatabricksCleanRoomSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    clean_rooms = get(api_session)
    transformed = transform(clean_rooms, workspace_id)
    load_clean_rooms(
        neo4j_session, transformed, workspace_id, common_job_parameters["UPDATE_TAG"]
    )


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """Paginate clean rooms.

    The endpoint returns 400/403 when external OpenSharing is disabled on the
    metastore; that is expected and skippable, so it never aborts the sync.
    """
    results: list[dict[str, Any]] = []
    params: dict[str, Any] = {"page_size": 100}
    while True:
        try:
            response = api_session.get("/api/2.0/clean-rooms", params=params)
        except requests.HTTPError as e:
            skip_or_raise_http(e, 400, 403)
            logger.info("Clean Rooms unavailable (OpenSharing disabled?): %s", e)
            break
        results.extend(response.get("clean_rooms", []) or [])
        next_token = response.get("next_page_token")
        if not next_token:
            break
        params = {"page_size": 100, "page_token": next_token}
    return results


@timeit
def transform(
    clean_rooms: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for c in clean_rooms:
        name = c.get("name")
        if not name:
            raise ValueError("Databricks clean room returned with empty name")
        result.append(
            {
                "id": scoped_id(workspace_id, name),
                "name": name,
                "owner": c.get("owner"),
                "comment": c.get("comment"),
                "access_restricted": c.get("access_restricted"),
                "created_at": epoch_ms_to_datetime(c.get("created_at")),
                "updated_at": epoch_ms_to_datetime(c.get("updated_at")),
            }
        )
    return result


@timeit
def load_clean_rooms(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksCleanRoomSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksCleanRoomSchema(), common_job_parameters).run(
        neo4j_session
    )
