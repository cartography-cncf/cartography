"""
Ingest the OAuth credentials that let LangSmith agents act on a human's behalf.

An agent obtains a token from a configured third-party OAuth provider, scoped to the human
who authorized it, and can then call that provider's API as them. This module inventories
those grants: which agent, on behalf of which user, against which provider, with what
scopes and expiry.

Only metadata is collected. No access token, refresh token or client secret is requested,
and none is returned by the endpoints used here.
"""

import logging
import re
from typing import Any

import neo4j

from cartography.intel.langsmith.util import cleanup_workspaces
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.util import load_by_workspace
from cartography.intel.langsmith.util import resolve_ls_user_id
from cartography.models.langsmith.agent import LangSmithAgentSchema
from cartography.models.langsmith.agentcredential import LangSmithAgentCredentialSchema
from cartography.models.langsmith.oauthprovider import LangSmithOAuthProviderSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Agent auth keys connections on assistant ids, which LangGraph issues as UUIDs. Agent
# registry ids are user-chosen slugs the route can't resolve: it answers 500 for them.
_ASSISTANT_ID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    workspaces: list[dict[str, Any]],
    agents: list[dict[str, Any]],
    user_lookup: dict[str, str],
    agents_readable: set[str],
    common_job_parameters: dict[str, Any],
) -> None:
    workspace_ids = [workspace["id"] for workspace in workspaces]
    providers, providers_readable = get_providers(client, org_id, workspace_ids)
    connections, connections_readable = get_connections(
        client, org_id, agents, workspace_ids
    )
    # Resolve each credential's provider slug to that provider's UUID within this
    # organization. Slugs are operator-chosen, so matching on one would happily link a
    # credential to another organization's identically named provider.
    provider_uuid_by_slug = {
        provider["provider_id"]: provider["id"] for provider in providers
    }
    credentials = transform_credentials(
        connections, user_lookup, provider_uuid_by_slug, org_id
    )
    # A credential can name an agent that no listing reported, so top up the inventory.
    extra_agents = transform_missing_agents(credentials, agents)

    load_agent_auth(
        neo4j_session,
        agents + extra_agents,
        providers,
        credentials,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_workspaces(
        neo4j_session,
        LangSmithOAuthProviderSchema(),
        providers_readable,
        common_job_parameters,
    )
    # Agents are loaded from the registry, from deployments, and from the credentials
    # that name them, so a workspace's agents are complete only when all three are.
    agents_complete = agents_readable & connections_readable
    # A credential's FOR_PROVIDER edge is resolved through the provider listing, so
    # cleaning credentials after a failed provider fetch would prune those edges.
    cleanup_workspaces(
        neo4j_session,
        LangSmithAgentCredentialSchema(),
        agents_complete & providers_readable,
        common_job_parameters,
    )
    cleanup_workspaces(
        neo4j_session, LangSmithAgentSchema(), agents_complete, common_job_parameters
    )


@timeit
def get_providers(
    client: LangSmithClient,
    org_id: str,
    workspace_ids: list[str],
) -> tuple[list[dict[str, Any]], set[str]]:
    """
    Fetch the OAuth providers agents can obtain tokens from, per workspace.

    Returns one record per provider per workspace that lists it, and the workspaces whose
    listings completed. The route is gated on the workspace-scoped deployments:read
    permission, so it is called in every workspace.
    """
    providers: dict[tuple[str, str], dict[str, Any]] = {}
    readable_workspace_ids: set[str] = set()
    for workspace_id in workspace_ids:
        readable = True
        for path, is_platform in (
            ("/v2/auth/providers", False),
            ("/v2/auth/platform-providers", True),
        ):
            try:
                rows = client.get(
                    path, org_id=org_id, tenant_id=workspace_id, host=True
                )
            except LangSmithFetchError as err:
                logger.warning(
                    "Skipping LangSmith %s for workspace %s: %s",
                    path,
                    workspace_id,
                    err,
                )
                readable = readable and err.not_found
                continue
            for row in rows:
                providers[(row["id"], workspace_id)] = {
                    **transform_provider(row, is_platform=is_platform),
                    "workspace_id": workspace_id,
                }
        if readable:
            readable_workspace_ids.add(workspace_id)
    return list(providers.values()), readable_workspace_ids


@timeit
def get_connections(
    client: LangSmithClient,
    org_id: str,
    agents: list[dict[str, Any]],
    workspace_ids: list[str],
) -> tuple[list[dict[str, Any]], set[str]]:
    """
    Fetch each agent's OAuth connections in each workspace the agent was seen in.

    This route takes the agent from the path rather than from the caller's identity, so it
    gives the organization-wide view of which agent holds which user's token. Returns the
    connections and the workspaces in which every agent's connections could be read.
    """
    connections: dict[str, dict[str, Any]] = {}
    readable_workspace_ids = set(workspace_ids)
    for agent_id, workspace_id in sorted(
        {
            (agent["agent_id"], agent["workspace_id"])
            for agent in agents
            if _ASSISTANT_ID.match(agent["agent_id"] or "")
        }
    ):
        try:
            payload = client.get(
                f"/v2/auth/agents/{agent_id}/connections",
                org_id=org_id,
                tenant_id=workspace_id,
                host=True,
            )
        except LangSmithFetchError as err:
            # 404 means agent auth has never seen this agent: it holds no
            # connections. Anything else hides connections that may exist.
            if not err.not_found:
                logger.warning(
                    "Skipping LangSmith connections for agent %s in workspace %s: %s",
                    agent_id,
                    workspace_id,
                    err,
                )
                readable_workspace_ids.discard(workspace_id)
            continue
        for row in payload.get("data") or []:
            connections.setdefault(row["id"], {**row, "workspace_id": workspace_id})
    return list(connections.values()), readable_workspace_ids


def transform_provider(
    provider: dict[str, Any],
    is_platform: bool,
) -> dict[str, Any]:
    """Shape an OAuth provider for ingest. Client secrets are not returned by the API."""
    return {
        "id": provider["id"],
        "provider_id": provider["provider_id"],
        "name": provider.get("name"),
        "provider_type": provider.get("provider_type"),
        "client_id": provider.get("client_id"),
        "auth_url": provider.get("auth_url"),
        "token_url": provider.get("token_url"),
        "mcp_server_url": provider.get("mcp_server_url"),
        "uses_pkce": provider.get("uses_pkce"),
        "token_endpoint_auth_method": provider.get("token_endpoint_auth_method"),
        "is_dynamic_client": provider.get("is_dynamic_client"),
        "allowed_redirect_uris": provider.get("allowed_redirect_uris") or [],
        "is_platform_provider": is_platform,
        "created_at": provider.get("created_at"),
        "updated_at": provider.get("updated_at"),
    }


def transform_credentials(
    connections: list[dict[str, Any]],
    user_lookup: dict[str, str],
    provider_uuid_by_slug: dict[str, str],
    org_id: str,
) -> list[dict[str, Any]]:
    """
    Shape agent connections for ingest.

    created_by names the human who authorized the connection. It is not documented which
    identifier it carries, and it has been observed as a user id, an email address and a
    bare username, so it is resolved through a lookup covering all of those.

    oauth_token_id is an opaque reference to the stored token; no token material is present
    in this payload and none is requested.
    """
    transformed = []
    for connection in connections:
        transformed.append(
            {
                "id": connection["id"],
                # Namespaced to match the agent node: agent ids are chosen by users, so
                # two organizations can pick the same one.
                "agent_id": (
                    f"{org_id}|{connection['agent_id']}"
                    if connection.get("agent_id")
                    else None
                ),
                "raw_agent_id": connection.get("agent_id"),
                "provider_id": connection.get("provider_id"),
                "provider_uuid": (
                    provider_uuid_by_slug.get(connection["provider_id"])
                    if connection.get("provider_id")
                    else None
                ),
                "workspace_id": connection["workspace_id"],
                "provider_account_label": connection.get("provider_account_label"),
                "scopes": connection.get("scopes") or [],
                "expires_at": connection.get("expires_at"),
                "oauth_token_id": connection.get("oauth_token_id"),
                "created_at": connection.get("created_at"),
                "owner_ls_user_id": resolve_ls_user_id(
                    connection.get("created_by"), user_lookup
                ),
            }
        )
    return transformed


def transform_missing_agents(
    credentials: list[dict[str, Any]],
    known_agents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create agent rows for agents a credential names but no listing reported."""
    known = {(agent["id"], agent["workspace_id"]) for agent in known_agents}
    extra: dict[tuple[str, str], dict[str, Any]] = {}
    for credential in credentials:
        agent_id = credential.get("agent_id")
        if not agent_id:
            continue
        key = (agent_id, credential["workspace_id"])
        if key in known or key in extra:
            continue
        extra[key] = {
            "id": agent_id,
            "agent_id": credential.get("raw_agent_id"),
            "workspace_id": credential["workspace_id"],
            "environments": [],
            "deployment_ids": [],
        }
    return list(extra.values())


@timeit
def load_agent_auth(
    neo4j_session: neo4j.Session,
    agents: list[dict[str, Any]],
    providers: list[dict[str, Any]],
    credentials: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    # Agents and providers must land before credentials so the credential edges match.
    load_by_workspace(neo4j_session, LangSmithAgentSchema(), agents, org_id, update_tag)
    load_by_workspace(
        neo4j_session, LangSmithOAuthProviderSchema(), providers, org_id, update_tag
    )
    load_by_workspace(
        neo4j_session, LangSmithAgentCredentialSchema(), credentials, org_id, update_tag
    )
