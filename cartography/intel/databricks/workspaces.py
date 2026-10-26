from typing import Any
from urllib.parse import urlparse

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.databricks.account_workspaces import load_account_links
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.models.databricks.workspace import DatabricksWorkspaceSchema
from cartography.models.databricks.workspace import (
    LegacyHostKeyedWorkspaceCleanupSchema,
)
from cartography.models.databricks.workspace import LegacyHostKeyedWorkspaceRel
from cartography.util import timeit

# The response header that carries the numeric workspace id on every workspace
# API call, on AWS, Azure and GCP alike.
_WORKSPACE_ID_HEADER = "x-databricks-org-id"


# DEPRECATED: host-keyed workspace nodes from earlier versions are migrated
# through this id; will be removed in v1.0.0.
def _legacy_workspace_id(host: str) -> str:
    """Return the host-derived id workspaces were keyed on before numeric ids."""
    parsed = urlparse(host if "://" in host else f"https://{host}")
    return (parsed.netloc or parsed.path).lower()


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    common_job_parameters: dict[str, Any],
    account_id: str | None = None,
) -> dict[str, Any]:
    workspace = get(api_session)
    load_workspaces(
        neo4j_session,
        [workspace],
        common_job_parameters["UPDATE_TAG"],
        account_id,
    )
    return workspace


@timeit
def get(api_session: DatabricksWorkspaceClient) -> dict[str, Any]:
    """Build a workspace summary from its numeric id and token settings.

    The node is keyed on the numeric workspace id rather than the host: the
    account API reports the same id, while hosts vary (Azure, private link,
    vanity URLs) and cannot be derived from the account API.
    """
    token_conf, headers = api_session.get_with_headers(
        "/api/2.0/workspace-conf",
        params={"keys": "enableTokensConfig,maxTokenLifetimeDays"},
    )
    workspace_id = headers.get(_WORKSPACE_ID_HEADER)
    if not workspace_id:
        raise ValueError(
            f"Databricks workspace {api_session.host} returned no "
            f"{_WORKSPACE_ID_HEADER} header, so its workspace id is unknown.",
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
        "workspace_id": workspace_id,
        "legacy_id": _legacy_workspace_id(api_session.host),
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
    account_id: str | None = None,
) -> None:
    load(neo4j_session, DatabricksWorkspaceSchema(), data, lastupdated=update_tag)
    for workspace in data:
        load_matchlinks(
            neo4j_session,
            LegacyHostKeyedWorkspaceRel(),
            [workspace],
            lastupdated=update_tag,
            WORKSPACE_ID=workspace["id"],
            _sub_resource_label="DatabricksWorkspace",
            _sub_resource_id=workspace["id"],
        )
    if account_id is not None:
        load_account_links(neo4j_session, data, account_id, update_tag)


# DEPRECATED: migration of host-keyed workspace nodes will be removed in v1.0.0.
@timeit
def cleanup_legacy_workspace(
    neo4j_session: neo4j.Session, workspace_id: str, update_tag: int
) -> None:
    """Delete the host-keyed node this workspace had, with everything under it."""
    GraphJob.from_node_schema(
        LegacyHostKeyedWorkspaceCleanupSchema(),
        {"UPDATE_TAG": update_tag, "WORKSPACE_ID": workspace_id},
        cascade_delete=True,
    ).run(neo4j_session)
