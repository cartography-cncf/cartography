from typing import Any
from urllib.parse import urlparse

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.models.databricks.workspace import DatabricksWorkspaceSchema
from cartography.util import timeit


def _workspace_id_from_host(host: str) -> str:
    """Derive a stable workspace identifier from the workspace host URL.

    Uses the host's deployment hostname (e.g. ``dbc-aaeaddda-e52f.cloud.databricks.com``)
    which is the natural unique key Databricks exposes to PAT-scoped clients.
    """
    parsed = urlparse(host if "://" in host else f"https://{host}")
    return (parsed.netloc or parsed.path).lower()


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    common_job_parameters: dict[str, Any],
) -> dict[str, Any]:
    workspace = get(api_session)
    load_workspaces(neo4j_session, [workspace], common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return workspace


@timeit
def get(api_session: DatabricksWorkspaceClient) -> dict[str, Any]:
    """Build a workspace summary from the host URL and token management settings."""
    workspace_id = _workspace_id_from_host(api_session.host)
    token_conf = api_session.get(
        "/api/2.0/workspace-conf",
        params={"keys": "enableTokensConfig,maxTokenLifetimeDays"},
    )
    enable_tokens = token_conf.get("enableTokensConfig")
    max_lifetime = token_conf.get("maxTokenLifetimeDays")
    # Databricks treats ``maxTokenLifetimeDays == "0"`` as a sentinel meaning
    # "revert to the system default" (730 days as of 2026-06), not a literal
    # zero-day lifetime. Map "" and "0" to None so security queries comparing
    # the explicit cap stay correct.
    parsed_lifetime: int | None
    if max_lifetime in (None, "", "0"):
        parsed_lifetime = None
    else:
        parsed_lifetime = int(max_lifetime)
    return {
        "id": workspace_id,
        "host": api_session.host,
        "tokens_enabled": (
            str(enable_tokens).lower() == "true" if enable_tokens is not None else None
        ),
        "max_token_lifetime_days": parsed_lifetime,
    }


@timeit
def load_workspaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksWorkspaceSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksWorkspaceSchema(), common_job_parameters).run(
        neo4j_session
    )
