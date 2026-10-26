from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.workspace import DatabricksAccountToWorkspaceRel
from cartography.models.databricks.workspace import DatabricksAccountWorkspaceSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> list[str]:
    """Load DatabricksWorkspace rows for every workspace the account owns.

    Returns the numeric workspace ids, which the workspace-assignments sync
    iterates.
    """
    workspaces = get(api_session)
    transformed = transform(workspaces)
    load_workspaces(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    return [row["id"] for row in transformed]


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.get(api_session.account_uri("/workspaces"))


@timeit
def transform(workspaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for w in workspaces:
        numeric_id = w.get("workspace_id")
        if numeric_id is None:
            continue
        result.append(
            {
                "id": str(numeric_id),
                "workspace_id": str(numeric_id),
                "deployment_name": w.get("deployment_name"),
                "workspace_name": w.get("workspace_name"),
            }
        )
    return result


@timeit
def load_workspaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksAccountWorkspaceSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def load_account_links(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    """Link each workspace in ``data`` to the account that owns it."""
    if not data:
        return
    load_matchlinks(
        neo4j_session,
        DatabricksAccountToWorkspaceRel(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
        _sub_resource_label="DatabricksAccount",
        _sub_resource_id=account_id,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, account_id: str, update_tag: int) -> None:
    """Delete workspaces the account no longer lists, with their resources.

    This also removes the host-keyed workspace nodes earlier versions created,
    since nothing refreshes them any more. Runs before the MatchLink cleanup so
    a stale workspace is still attached to the account when it is matched.
    """
    GraphJob.from_node_schema(
        DatabricksAccountWorkspaceSchema(),
        {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id},
        cascade_delete=True,
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        DatabricksAccountToWorkspaceRel(),
        "DatabricksAccount",
        account_id,
        update_tag,
    ).run(neo4j_session)
