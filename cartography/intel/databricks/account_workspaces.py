from typing import Any
from urllib.parse import urlparse

import neo4j

from cartography.client.core.tx import load
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.workspace import DatabricksWorkspaceSchema
from cartography.util import timeit


def _workspace_host_suffix(account_host: str) -> str:
    """Derive the per-workspace host suffix from the account host.

    The account console host mirrors the workspace host domain:
    ``accounts.cloud.databricks.com`` (AWS) -> workspaces at
    ``<deployment>.cloud.databricks.com``; ``accounts.gcp.databricks.com`` (GCP)
    -> ``<deployment>.gcp.databricks.com``. Stripping the leading ``accounts.``
    yields the suffix, so GCP workspaces get the right node id (and collide with
    the workspace-API node) instead of a hardcoded AWS suffix.
    """
    netloc = (urlparse(account_host).netloc or account_host).lower()
    prefix = "accounts."
    return netloc[len(prefix) :] if netloc.startswith(prefix) else netloc


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> dict[str, str]:
    """Load DatabricksWorkspace rows for every workspace the account owns.

    Returns a mapping of the numeric account-API workspace id (as a string) to
    the workspace's deployment-host node id, so the workspace-assignments sync
    can resolve the numeric id the permissions API reports back to the node key.

    Deliberately runs no cleanup: the workspace-API sync owns DatabricksWorkspace
    lifecycle. Here we only enrich the account-owned workspaces with their
    numeric id / deployment / name and the DatabricksAccount -> RESOURCE edge.
    """
    workspaces = get(api_session)
    transformed = transform(workspaces, _workspace_host_suffix(api_session.host))
    load_workspaces(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    return {row["workspace_id"]: row["id"] for row in transformed}


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.get(api_session.account_uri("/workspaces"))


@timeit
def transform(
    workspaces: list[dict[str, Any]], host_suffix: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for w in workspaces:
        deployment_name = w.get("deployment_name")
        numeric_id = w.get("workspace_id")
        if not deployment_name or numeric_id is None:
            continue
        host_id = f"{deployment_name}.{host_suffix}".lower()
        result.append(
            {
                # Node id is the deployment host so it collides with the same
                # workspace ingested by the workspace-API sync (which keys on the
                # host too), letting both paths enrich the same node.
                "id": host_id,
                "workspace_id": str(numeric_id),
                "deployment_name": deployment_name,
                "workspace_name": w.get("workspace_name"),
                "host": f"https://{host_id}",
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
        DatabricksWorkspaceSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
