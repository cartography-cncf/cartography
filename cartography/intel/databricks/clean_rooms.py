import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import skip_or_raise_http
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.clean_room import DatabricksCleanRoomSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    metastore_id: str,
    common_job_parameters: dict[str, Any],
) -> bool:
    """Sync clean rooms. Returns whether the fetch was complete.

    Returns False when the listing was skipped (external OpenSharing disabled),
    signalling that the caller must NOT clean up clean rooms: a skip is not proof
    that none exist, so purging would delete previously ingested nodes.
    """
    clean_rooms, complete = get(api_session)
    transformed = transform(clean_rooms, metastore_id)
    load_clean_rooms(
        neo4j_session, transformed, workspace_id, common_job_parameters["UPDATE_TAG"]
    )
    return complete


@timeit
def get(api_session: DatabricksWorkspaceClient) -> tuple[list[dict[str, Any]], bool]:
    """Paginate clean rooms. Returns ``(clean_rooms, complete)``.

    ``complete`` is False when the endpoint returns 400/403 (external OpenSharing
    disabled on the metastore): a skip, not a genuine empty result, so cleanup is
    unsafe.
    """
    results: list[dict[str, Any]] = []
    params: dict[str, Any] = {"page_size": 100}
    seen_tokens: set[str] = set()
    while True:
        try:
            response = api_session.get("/api/2.0/clean-rooms", params=params)
        except requests.HTTPError as e:
            skip_or_raise_http(e, 400, 403)
            logger.warning(
                "Clean Rooms listing skipped (external OpenSharing disabled?); "
                "not cleaning up clean rooms this run: %s",
                e,
            )
            return [], False
        results.extend(response.get("clean_rooms", []) or [])
        next_token = response.get("next_page_token")
        if not next_token:
            break
        if next_token in seen_tokens:
            raise ValueError(
                f"Databricks clean-rooms list repeated page token {next_token!r}; "
                "aborting to avoid an infinite loop.",
            )
        seen_tokens.add(next_token)
        params = {"page_size": 100, "page_token": next_token}
    return results, True


@timeit
def transform(
    clean_rooms: list[dict[str, Any]], metastore_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for c in clean_rooms:
        name = c.get("name")
        if not name:
            raise ValueError("Databricks clean room returned with empty name")
        result.append(
            {
                "id": uc_id(metastore_id, name),
                "name": name,
                "metastore_id": metastore_id,
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
