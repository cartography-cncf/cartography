"""
Workspace-scoped resources: secrets, resource tags, OAuth clients and MCP servers.

These all need an ``X-Tenant-Id`` header and are fetched per workspace. A credential
commonly holds ``workspaces:read`` in only some workspaces, so each fetch degrades to a
warning rather than failing the module, and the resource type it belongs to skips cleanup.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.langsmith.util import cleanup_if_complete
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.models.core.nodes import CartographyNodeSchema
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
    secrets_complete = tags_complete = oauth_clients_complete = mcp_servers_complete = (
        True
    )

    for workspace in workspaces:
        workspace_id = workspace["id"]

        raw_secrets, ok = get_secrets(client, org_id, workspace_id)
        secrets.extend(transform_secrets(workspace_id, raw_secrets))
        secrets_complete = secrets_complete and ok

        rows, ok = get_tags(client, org_id, workspace_id)
        tags.extend(rows)
        tags_complete = tags_complete and ok

        rows, ok = get_oauth_clients(client, org_id, workspace_id)
        oauth_clients.extend(rows)
        oauth_clients_complete = oauth_clients_complete and ok

        rows, ok = get_mcp_servers(client, org_id, workspace_id)
        mcp_servers.extend(rows)
        mcp_servers_complete = mcp_servers_complete and ok

    load_workspace_resources(
        neo4j_session,
        secrets,
        tags,
        oauth_clients,
        mcp_servers,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(
        neo4j_session,
        common_job_parameters,
        [
            (LangSmithSecretSchema(), secrets_complete),
            (LangSmithResourceTagSchema(), tags_complete),
            (LangSmithOAuthClientSchema(), oauth_clients_complete),
            (LangSmithMcpServerSchema(), mcp_servers_complete),
        ],
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
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith secrets for workspace %s: %s", workspace_id, err
        )
        return [], err.not_found


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
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch the workspace's attribute-based access control tag vocabulary."""
    try:
        tag_keys = client.get(
            "/api/v1/workspaces/current/tag-keys",
            org_id=org_id,
            tenant_id=workspace_id,
        )
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith resource tags for workspace %s: %s", workspace_id, err
        )
        return [], err.not_found

    tags = []
    complete = True
    for tag_key in tag_keys:
        try:
            tag_values = client.get(
                f"/api/v1/workspaces/current/tag-keys/{tag_key['id']}/tag-values",
                org_id=org_id,
                tenant_id=workspace_id,
            )
        except LangSmithFetchError as err:
            logger.warning(
                "Skipping LangSmith tag values for tag key %s: %s", tag_key["id"], err
            )
            complete = complete and err.not_found
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
    return tags, complete


@timeit
def get_oauth_clients(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch third-party apps registered to call the LangSmith API through OAuth."""
    try:
        payload = client.get(
            "/api/v1/platform/oauth/clients",
            org_id=org_id,
            tenant_id=workspace_id,
        )
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith OAuth clients for workspace %s: %s", workspace_id, err
        )
        return [], err.not_found
    clients = payload.get("clients") or []
    for oauth_client in clients:
        oauth_client["workspace_id"] = workspace_id
    return clients, True


@timeit
def get_mcp_servers(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch the vendor-managed MCP gateways a workspace exposes.

    Each MCP vendor is listed first, then its gateways, because the gateway route is
    keyed by vendor slug.
    """
    try:
        vendor_payload = client.get(
            "/api/v1/platform/mcp-vendors", org_id=org_id, tenant_id=workspace_id
        )
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith MCP vendors for workspace %s: %s", workspace_id, err
        )
        return [], err.not_found

    servers: list[dict[str, Any]] = []
    complete = True
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
        except LangSmithFetchError as err:
            logger.warning(
                "Skipping LangSmith MCP gateways for vendor %s in workspace %s: %s",
                vendor_slug,
                workspace_id,
                err,
            )
            complete = complete and err.not_found
            continue
        except requests.HTTPError as err:
            # A vendor that is registered but not yet OAuth-connected in this workspace
            # answers 400 ("Please connect your Arcade account first"). It exposes no
            # gateways, so treat it as empty rather than failing the whole sync.
            if err.response is not None and err.response.status_code == 400:
                logger.warning(
                    "Skipping LangSmith MCP gateways for vendor %s in workspace %s: "
                    "the vendor is not connected (%s)",
                    vendor_slug,
                    workspace_id,
                    err,
                )
                continue
            raise
        for gateway in gateways:
            servers.append(
                _transform_mcp_server(gateway, workspace_id, vendor=vendor_slug)
            )
    return servers, complete


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
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    schemas: list[tuple[CartographyNodeSchema, bool]],
) -> None:
    for schema, complete in schemas:
        cleanup_if_complete(neo4j_session, schema, complete, common_job_parameters)
