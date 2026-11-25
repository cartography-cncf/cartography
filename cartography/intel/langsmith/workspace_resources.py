"""
Workspace-scoped resources: secrets, resource tags, tracing projects, OAuth clients and
MCP servers, plus the resource tags applied to projects and deployments.

These all need an ``X-Tenant-Id`` header and are fetched per workspace. A credential
commonly holds ``workspaces:read`` in only some workspaces, so each fetch degrades to a
warning rather than failing the module, and the resource type it belongs to skips cleanup.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.langsmith.util import cleanup_if_complete
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.langsmith.deployment import LangSmithDeploymentToResourceTagRel
from cartography.models.langsmith.mcpserver import LangSmithMcpServerSchema
from cartography.models.langsmith.oauthclient import LangSmithOAuthClientSchema
from cartography.models.langsmith.project import LangSmithProjectSchema
from cartography.models.langsmith.project import LangSmithProjectToResourceTagRel
from cartography.models.langsmith.resourcetag import LangSmithResourceTagSchema
from cartography.models.langsmith.secret import LangSmithSecretSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# The tracing project listing caps `limit` at 100.
_PROJECT_PAGE_SIZE = 100

# Tag value IDs applied to each resource, keyed by the taggings listing's resource type
# (for example "projects") and then by resource ID.
Taggings = dict[str, dict[str, list[str]]]


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
    project_tags: list[dict[str, Any]] = []
    deployment_tags: list[dict[str, Any]] = []
    secrets_complete = tags_complete = True
    oauth_clients_complete = mcp_servers_complete = taggings_complete = True

    for workspace in workspaces:
        workspace_id = workspace["id"]

        raw_secrets, ok = get_secrets(client, org_id, workspace_id)
        secrets.extend(transform_secrets(workspace_id, raw_secrets))
        secrets_complete = secrets_complete and ok

        rows, ok = get_tags(client, org_id, workspace_id)
        tags.extend(rows)
        tags_complete = tags_complete and ok

        # A resource whose taggings couldn't be read must not lose its TAGGED edges in
        # cleanup: a dropped tag could hide a deny policy.
        taggings, taggings_ok = get_taggings(client, org_id, workspace_id)

        rows, ok = get_projects(client, org_id, workspace_id)
        load(
            neo4j_session,
            LangSmithProjectSchema(),
            rows,
            ORG_ID=org_id,
            WORKSPACE_ID=workspace_id,
            lastupdated=common_job_parameters["UPDATE_TAG"],
        )
        if ok:
            GraphJob.from_node_schema(
                LangSmithProjectSchema(),
                {**common_job_parameters, "WORKSPACE_ID": workspace_id},
            ).run(neo4j_session)

        rows, ok = get_oauth_clients(client, org_id, workspace_id)
        oauth_clients.extend(rows)
        oauth_clients_complete = oauth_clients_complete and ok

        rows, ok = get_mcp_servers(client, org_id, workspace_id)
        mcp_servers.extend(rows)
        mcp_servers_complete = mcp_servers_complete and ok

        project_tags.extend(transform_project_tags(taggings.get("projects", {})))
        deployment_tags.extend(
            transform_deployment_tags(taggings.get("deployments", {}))
        )
        taggings_complete = taggings_complete and taggings_ok

    load_workspace_resources(
        neo4j_session,
        secrets,
        tags,
        oauth_clients,
        mcp_servers,
        project_tags,
        deployment_tags,
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
        taggings_complete,
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
def get_taggings(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> tuple[Taggings, bool]:
    """
    Fetch the workspace's taggings: which tag values are applied to which resources.

    The listing groups each tag value's resources by type, such as projects and deployments. It's inverted here so each resource can look up its tag values.
    """
    try:
        payload = client.get(
            "/api/v1/workspaces/current/taggings",
            org_id=org_id,
            tenant_id=workspace_id,
        )
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith resource taggings for workspace %s: %s",
            workspace_id,
            err,
        )
        return {}, err.not_found

    taggings: Taggings = {}
    for tagging in payload:
        for resource_type, resources in (tagging.get("resources") or {}).items():
            by_resource = taggings.setdefault(resource_type, {})
            for resource in resources or []:
                by_resource.setdefault(resource["resource_id"], []).append(
                    tagging["tag_value_id"]
                )
    return taggings, True


@timeit
def get_projects(
    client: LangSmithClient,
    org_id: str,
    workspace_id: str,
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch the workspace's tracing projects."""
    try:
        projects = client.get_paginated(
            "/api/v1/sessions",
            params={"reference_free": "true", "skip_enrichment": "true"},
            org_id=org_id,
            tenant_id=workspace_id,
            page_size=_PROJECT_PAGE_SIZE,
        )
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith projects for workspace %s: %s", workspace_id, err
        )
        return [], err.not_found

    return [
        {
            "id": project["id"],
            "name": project.get("name"),
            "description": project.get("description"),
            "start_time": project.get("start_time"),
            "trace_tier": project.get("trace_tier"),
            "workspace_id": workspace_id,
        }
        for project in projects
    ], True


def transform_project_tags(
    tag_value_ids: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Flatten the tag values applied to each project into one record per edge."""
    return [
        {"project_id": project_id, "tag_value_id": tag_value_id}
        for project_id, values in tag_value_ids.items()
        for tag_value_id in values
    ]


def transform_deployment_tags(
    tag_value_ids: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Flatten the tag values applied to each deployment into one record per edge."""
    return [
        {"deployment_id": deployment_id, "tag_value_id": tag_value_id}
        for deployment_id, values in tag_value_ids.items()
        for tag_value_id in values
    ]


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
    client: LangSmithClient,
    org_id: str,
    workspace_id: str,
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
            servers.append(_transform_mcp_server(gateway, workspace_id, vendor_slug))
    return servers, complete


def _transform_mcp_server(
    server: dict[str, Any],
    workspace_id: str,
    vendor: str | None,
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
    project_tags: list[dict[str, Any]],
    deployment_tags: list[dict[str, Any]],
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
    for rel, records in (
        (LangSmithProjectToResourceTagRel(), project_tags),
        (LangSmithDeploymentToResourceTagRel(), deployment_tags),
    ):
        load_matchlinks(
            neo4j_session,
            rel,
            records,
            lastupdated=update_tag,
            _sub_resource_label="LangSmithOrganization",
            _sub_resource_id=org_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    schemas: list[tuple[CartographyNodeSchema, bool]],
    taggings_complete: bool,
) -> None:
    for schema, complete in schemas:
        cleanup_if_complete(neo4j_session, schema, complete, common_job_parameters)
    if not taggings_complete:
        logger.warning(
            "Skipping LangSmith project and deployment tag cleanup for organization %s: "
            "collection was incomplete.",
            common_job_parameters["ORG_ID"],
        )
        return
    for rel in (
        LangSmithProjectToResourceTagRel(),
        LangSmithDeploymentToResourceTagRel(),
    ):
        GraphJob.from_matchlink(
            rel,
            "LangSmithOrganization",
            common_job_parameters["ORG_ID"],
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)
