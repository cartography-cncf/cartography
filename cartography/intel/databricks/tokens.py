from datetime import datetime
from datetime import timezone
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.token import DatabricksTokenSchema
from cartography.util import timeit


def _scoped_or_none(workspace_id: str, value: Any) -> str | None:
    if value is None:
        return None
    return scoped_id(workspace_id, str(value))


def _epoch_ms_to_datetime(value: Any) -> datetime | None:
    """Convert a Unix-epoch-milliseconds value to a UTC datetime.

    The Databricks token-management API encodes ``expiry_time = -1`` as a
    sentinel for "no expiry"; both that and a missing value yield ``None``.
    """
    if value in (None, -1):
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    tokens = get(api_session)
    transformed = transform(tokens, workspace_id)
    load_tokens(
        neo4j_session, transformed, workspace_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    response = api_session.get("/api/2.0/token-management/tokens")
    return response.get("token_infos", []) or []


@timeit
def transform(tokens: list[dict[str, Any]], workspace_id: str) -> list[dict[str, Any]]:
    """Scope token ids to the workspace.

    The token-management API returns workspace-scoped ``token_id`` strings and
    integer ``owner_id`` / ``created_by_id`` referencing SCIM principals. Both
    are namespaced under the workspace so multi-workspace ingestion cannot
    collapse same-id tokens, and OWNER_OF MATCH lines up with the composite
    ``DatabricksUser.id`` / ``DatabricksServicePrincipal.id``.
    """
    result: list[dict[str, Any]] = []
    for t in tokens:
        token_id = t["token_id"]
        result.append(
            {
                "id": scoped_id(workspace_id, token_id),
                "token_id": token_id,
                "comment": t.get("comment"),
                "creation_time": _epoch_ms_to_datetime(t.get("creation_time")),
                "expiry_time": _epoch_ms_to_datetime(t.get("expiry_time")),
                "owner_id": _scoped_or_none(workspace_id, t.get("owner_id")),
                "created_by_id": _scoped_or_none(workspace_id, t.get("created_by_id")),
                "created_by_username": t.get("created_by_username"),
            }
        )
    return result


@timeit
def load_tokens(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksTokenSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksTokenSchema(), common_job_parameters).run(
        neo4j_session
    )
