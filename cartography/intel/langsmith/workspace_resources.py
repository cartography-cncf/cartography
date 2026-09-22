"""
Workspace-scoped resources: secrets, resource tags, OAuth clients and MCP servers.

These all need an ``X-Tenant-Id`` header and are fetched per workspace. A credential
commonly holds ``workspaces:read`` in only some workspaces, so each fetch degrades to a
warning rather than failing the module.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithPermissionError
from cartography.models.langsmith.mcpserver import LangSmithMcpServerSchema
from cartography.models.langsmith.oauthclient import LangSmithOAuthClientSchema
from cartography.models.langsmith.resourcetag import LangSmithResourceTagSchema
from cartography.models.langsmith.secret import LangSmithSecretSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    workspaces: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    secrets: list[dict[str, Any]] = []
    tags: list[dict[str, Any]] = []
    oauth_clients: list[dict[str, Any]] = []
    mcp_servers: list[dict[str, Any]] = []

    complete = True
    for workspace in workspaces:
        workspace_id = workspace["id"]
        raw_secrets, secrets_ok = get_secrets(client, org_id, workspace_id)
        complete = complete and secrets_ok
        secrets.extend(transform_secrets(workspace_id, raw_secrets))
        tags.extend(get_tags(client, org_id, workspace_id))
        oauth_clients.extend(get_oauth_clients(client, org_id, workspace_id))
        mcp_servers.extend(get_mcp_servers(client, org_id, workspace_id))

    load_workspace_resources(
        neo4j_session,
        secrets,
        tags,
        oauth_clients,
        mcp_servers,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if complete:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping LangSmith workspace resource cleanup for organization %s: not every "
            "workspace could be read, so existing nodes are preserved.",
            org_id,
        )


@timeit
def get_secrets(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """
    List a workspace's secret key names.

    This deliberately uses /workspaces/current/secrets, which returns key names only. The
    sibling /secrets/encrypted route returns secret material and is never called.
    """
    try:
        return (
            client.get(
                "/api/v1/workspaces/current/secrets",
                org_id=org_id,
                tenant_id=workspace_id,
            ),
            True,
        )
    except LangSmithPermissionError as err:
        logger.warning(
            "Skipping LangSmith secrets for workspace %s: %s", workspace_id, err
        )
        return [], False


def transform_secrets(
    workspace_id: str, secrets: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{workspace_id}|{secret['key']}",
            "key": secret["key"],
            "workspace_id": workspace_id,
        }
        for secret in secrets
    ]


@timeit
def get_tags(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> list[dict[str, Any]]:
    """Fetch the workspace's attribute-based access control tag vocabulary."""
    try:
        tag_keys = client.get(
            "/api/v1/workspaces/current/tag-keys",
            org_id=org_id,
            tenant_id=workspace_id,
        )
    except LangSmithPermissionError as err:
        logger.warning(
            "Skipping LangSmith resource tags for workspace %s: %s", workspace_id, err
        )
        return []

    tags = []
    for tag_key in tag_keys:
        try:
            tag_values = client.get(
                f"/api/v1/workspaces/current/tag-keys/{tag_key['id']}/tag-values",
                org_id=org_id,
                tenant_id=workspace_id,
            )
        except LangSmithPermissionError as err:
            logger.warning(
                "Skipping LangSmith tag values for tag key %s: %s", tag_key["id"], err
            )
            continue
        for tag_value in tag_values:
            tags.append(
                {
                    "id": tag_value["id"],
                    "key": tag_key.get("key") or tag_key.get("name"),
                    "value": tag_value.get("value") or tag_value.get("name"),
                    "key_id": tag_key["id"],
                    "workspace_id": workspace_id,
                }
            )
    return tags


@timeit
def get_oauth_clients(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> list[dict[str, Any]]:
    """Fetch third-party apps registered to call the LangSmith API via OAuth."""
    try:
        payload = client.get(
            "/api/v1/platform/oauth/clients",
            org_id=org_id,
            tenant_id=workspace_id,
        )
    except LangSmithPermissionError as err:
        logger.warning(
            "Skipping LangSmith OAuth clients for workspace %s: %s", workspace_id, err
        )
        return []
    clients = payload.get("clients") or []
    for oauth_client in clients:
        oauth_client["workspace_id"] = workspace_id
    return clients


@timeit
def get_mcp_servers(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> list[dict[str, Any]]:
    """
    Fetch the vendor-managed MCP gateways a workspace exposes.

    Each MCP vendor is listed first, then its gateways, because the gateway route is
    keyed by vendor slug.
    """
    servers: list[dict[str, Any]] = []
    try:
        vendor_payload = client.get(
            "/api/v1/platform/mcp-vendors", org_id=org_id, tenant_id=workspace_id
        )
    except LangSmithPermissionError as err:
        logger.warning(
            "Skipping LangSmith MCP vendors for workspace %s: %s", workspace_id, err
        )
        return servers

    for vendor in vendor_payload.get("mcp_vendors") or []:
        vendor_slug = vendor.get("vendor_id") or vendor.get("name")
        if not vendor_slug:
            continue
        try:
            gateways = client.get_paginated_envelope(
                f"/api/v1/platform/mcp-vendors/{vendor_slug}/mcp-servers",
                key="items",
                org_id=org_id,
                tenant_id=workspace_id,
            )
        except LangSmithPermissionError as err:
            logger.debug(
                "Skipping LangSmith MCP gateways for vendor %s: %s", vendor_slug, err
            )
            continue
        for gateway in gateways:
            servers.append(
                _transform_mcp_server(gateway, workspace_id, vendor=vendor_slug)
            )
    return servers


def _transform_mcp_server(
    server: dict[str, Any], workspace_id: str, vendor: str | None
) -> dict[str, Any]:
    tool_filter = server.get("tool_filter") or {}
    return {
        "id": server["id"],
        "name": server.get("name"),
        "slug": server.get("slug"),
        "description": server.get("description"),
        "url": server.get("url"),
        "vendor": vendor,
        "auth_type": server.get("auth_type"),
        "status": server.get("status"),
        "tool_names": tool_filter.get("allowed") or tool_filter.get("tools") or [],
        "created_at": server.get("created_at"),
        "updated_at": server.get("updated_at"),
        "workspace_id": workspace_id,
    }


@timeit
def load_workspace_resources(
    neo4j_session: neo4j.Session,
    secrets: list[dict[str, Any]],
    tags: list[dict[str, Any]],
    oauth_clients: list[dict[str, Any]],
    mcp_servers: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    for schema, data in (
        (LangSmithSecretSchema(), secrets),
        (LangSmithResourceTagSchema(), tags),
        (LangSmithOAuthClientSchema(), oauth_clients),
        (LangSmithMcpServerSchema(), mcp_servers),
    ):
        load(neo4j_session, schema, data, lastupdated=update_tag, ORG_ID=org_id)


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    for schema in (
        LangSmithSecretSchema(),
        LangSmithResourceTagSchema(),
        LangSmithOAuthClientSchema(),
        LangSmithMcpServerSchema(),
    ):
        GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)
