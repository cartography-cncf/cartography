"""
Workspace resources: secrets, resource tags and MCP gateways, plus OAuth clients.

Secrets, tags and MCP gateways need an ``X-Tenant-Id`` header and are fetched per
workspace, and each workspace is their sub-resource. A credential commonly holds
``workspaces:read`` in only some workspaces, so a failed fetch degrades to a warning and
skips cleanup in that workspace alone. OAuth clients are registered against the
organization, so they are read once per organization.
"""

import logging
from collections import Counter
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.langsmith.util import cleanup_if_complete
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.util import load_by_workspace
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
    secrets: dict[str, list[dict[str, Any]]] = {}
    tags: dict[str, list[dict[str, Any]]] = {}
    mcp_servers: dict[str, list[dict[str, Any]]] = {}
    complete: dict[str, set[str]] = {"secrets": set(), "tags": set(), "mcp": set()}
    unconnected_vendors: Counter[str] = Counter()

    for workspace in workspaces:
        workspace_id = workspace["id"]

        raw_secrets, ok = get_secrets(client, org_id, workspace_id)
        secrets[workspace_id] = transform_secrets(workspace_id, raw_secrets)
        if ok:
            complete["secrets"].add(workspace_id)

        tags[workspace_id], ok = get_tags(client, org_id, workspace_id)
        if ok:
            complete["tags"].add(workspace_id)

        mcp_servers[workspace_id], ok = get_mcp_servers(
            client, org_id, workspace_id, unconnected_vendors=unconnected_vendors
        )
        if ok:
            complete["mcp"].add(workspace_id)

    if unconnected_vendors:
        logger.info(
            "LangSmith MCP gateways could not be listed in organization %s, so their "
            "cleanup is skipped: %s. The vendor answers from the syncing user's own "
            "connection to it, which the credential lacks.",
            org_id,
            ", ".join(
                f"{vendor} in {count} workspace(s)"
                for vendor, count in sorted(unconnected_vendors.items())
            ),
        )

    for schema, rows_by_workspace, complete_ids in (
        (LangSmithSecretSchema(), secrets, complete["secrets"]),
        (LangSmithResourceTagSchema(), tags, complete["tags"]),
        (LangSmithMcpServerSchema(), mcp_servers, complete["mcp"]),
    ):
        load_by_workspace(
            neo4j_session,
            schema,
            rows_by_workspace,
            complete_ids,
            common_job_parameters,
        )

    # OAuth clients belong to the organization, not to a workspace.
    oauth_clients, oauth_clients_complete = get_oauth_clients(client, org_id)
    load(
        neo4j_session,
        LangSmithOAuthClientSchema(),
        oauth_clients,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        ORG_ID=org_id,
    )
    cleanup_if_complete(
        neo4j_session,
        LangSmithOAuthClientSchema(),
        oauth_clients_complete,
        common_job_parameters,
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
    client: LangSmithClient, org_id: str
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch third-party apps registered to call the LangSmith API through OAuth.

    Clients are registered against the organization and the listing needs
    organization:read, so it is read once per organization. LangSmith answers 404 when
    the organization has not enabled the feature, which is an empty answer.
    """
    try:
        payload = client.get("/api/v1/platform/oauth/clients", org_id=org_id)
    except LangSmithFetchError as err:
        logger.warning("Skipping LangSmith OAuth clients: %s", err)
        return [], err.not_found
    return payload.get("clients") or [], True


@timeit
def get_mcp_servers(
    client: LangSmithClient,
    org_id: str,
    workspace_id: str,
    unconnected_vendors: Counter[str] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch the vendor-managed MCP gateways a workspace exposes.

    Each MCP vendor is listed first, then its gateways, because the gateway route is
    keyed by vendor slug. The vendor listing is a static catalog, and the gateway route
    proxies to the vendor using the calling user's own connection to it. A credential
    without one (any service key, or a user who never connected the vendor) gets a 400,
    which says nothing about whether gateways exist, so the listing is incomplete. That
    is the common case, so each one is tallied in ``unconnected_vendors`` for a single
    summary line rather than logged per workspace.
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
            status = err.response.status_code if err.response is not None else None
            if status == 501:
                # LangSmith lists this vendor in its catalog but cannot list gateways
                # for it, so there is nothing it could return.
                continue
            # The vendor answers 400 when the calling user has no connection to it
            # ("Please connect your Arcade account first"), when the workspace has no
            # vendor configuration, or when the caller has no user identity. Gateways
            # may still exist, so they must not be cleaned up.
            if status == 400:
                logger.debug(
                    "LangSmith MCP vendor %s could not list gateways in workspace %s: %s",
                    vendor_slug,
                    workspace_id,
                    err,
                )
                complete = False
                if unconnected_vendors is not None:
                    unconnected_vendors[vendor_slug] += 1
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
