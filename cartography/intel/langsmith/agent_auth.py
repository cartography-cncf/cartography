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
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.intel.langsmith.deployments import AgentCoverage
from cartography.intel.langsmith.util import cleanup_if_complete
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.util import resolve_ls_user_id
from cartography.intel.langsmith.util import run_preserving_cleanup
from cartography.models.langsmith.agent import LangSmithAgentSchema
from cartography.models.langsmith.agentcredential import LangSmithAgentCredentialSchema
from cartography.models.langsmith.oauthprovider import LangSmithOAuthProviderSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# An agent is kept when a deployment serving it could not be listed, or sits in a
# workspace whose deployments could not be read. An agent known only through a
# credential has no deployment, so it is kept whenever any connection listing failed.
_PRESERVE_AGENTS = (
    "EXISTS { MATCH (n)--(d:LangSmithDeployment) "
    "WHERE d.id IN $LANGSMITH_UNLISTED_DEPLOYMENT_IDS "
    "OR EXISTS { MATCH (d)<-[:CONTAINS]-(w:LangSmithWorkspace) "
    "WHERE w.id IN $LANGSMITH_UNREAD_WORKSPACE_IDS } } "
    "OR ($LANGSMITH_CONNECTIONS_INCOMPLETE "
    "AND NOT EXISTS { MATCH (n)--(:LangSmithDeployment) })"
)
# A credential is kept when its agent's connections were not read in full this run. A
# credential whose agent was deleted is an orphan and is cleaned up.
_PRESERVE_CREDENTIALS = "EXISTS { MATCH (n)--(a:LangSmithAgent) WHERE NOT a.id IN $LANGSMITH_READ_AGENT_IDS }"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    workspaces: list[dict[str, Any]],
    agents: list[dict[str, Any]],
    workspace_by_deployment: dict[str, str],
    user_lookup: dict[str, str],
    coverage: AgentCoverage,
    common_job_parameters: dict[str, Any],
) -> None:
    providers, providers_complete = get_providers(client, org_id, workspaces)
    connections, read_agent_ids, connections_complete = get_connections(
        client, org_id, agents, workspace_by_deployment
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
    # A credential can name an agent that no deployment reported, so top up the inventory.
    extra_agents = transform_missing_agents(credentials, agents)

    load_agent_auth(
        neo4j_session,
        agents + extra_agents,
        providers,
        credentials,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_if_complete(
        neo4j_session,
        LangSmithOAuthProviderSchema(),
        providers_complete,
        common_job_parameters,
    )
    # Agents first: a credential left without its agent is then an orphan, and the
    # credential cleanup below removes it in the same run.
    run_preserving_cleanup(
        neo4j_session,
        LangSmithAgentSchema(),
        common_job_parameters,
        _PRESERVE_AGENTS,
        {
            "LANGSMITH_UNLISTED_DEPLOYMENT_IDS": sorted(
                coverage.unlisted_deployment_ids
            ),
            "LANGSMITH_UNREAD_WORKSPACE_IDS": sorted(coverage.unread_workspace_ids),
            "LANGSMITH_CONNECTIONS_INCOMPLETE": not connections_complete,
        },
    )
    if connections_complete:
        # Agents known only through a credential were not queried themselves, but every
        # listing that could name them answered.
        read_agent_ids |= {agent["id"] for agent in extra_agents}
    # A credential's FOR_PROVIDER edge is resolved through the provider listing, so
    # cleaning credentials after a failed provider fetch would prune those edges.
    if not providers_complete:
        cleanup_if_complete(
            neo4j_session,
            LangSmithAgentCredentialSchema(),
            False,
            common_job_parameters,
        )
        return
    run_preserving_cleanup(
        neo4j_session,
        LangSmithAgentCredentialSchema(),
        common_job_parameters,
        _PRESERVE_CREDENTIALS,
        {"LANGSMITH_READ_AGENT_IDS": sorted(read_agent_ids)},
    )


@timeit
def get_providers(
    client: LangSmithClient,
    org_id: str,
    workspaces: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch the OAuth providers agents can obtain tokens from.

    Neither route depends on the workspace: /v2/auth/providers lists the organization's
    providers, and /v2/auth/platform-providers lists a global, platform-owned set. Both
    are gated on the workspace-scoped deployments:read permission, though, so each is
    tried workspace by workspace until one answers. The listing is complete once both
    have answered.
    """
    providers: dict[str, dict[str, Any]] = {}
    complete = True
    for path, is_platform in (
        ("/v2/auth/providers", False),
        ("/v2/auth/platform-providers", True),
    ):
        rows, ok = _first_readable(client, org_id, workspaces, path)
        complete = complete and ok
        for row in rows:
            providers[row["id"]] = transform_provider(row, is_platform=is_platform)
    return list(providers.values()), complete


def _first_readable(
    client: LangSmithClient,
    org_id: str,
    workspaces: list[dict[str, Any]],
    path: str,
) -> tuple[list[dict[str, Any]], bool]:
    """Read a workspace-independent listing through the first workspace that allows it."""
    denied: list[str] = []
    for workspace in workspaces:
        try:
            rows = client.get(path, org_id=org_id, tenant_id=workspace["id"], host=True)
        except LangSmithFetchError as err:
            if err.not_found:
                # The route is not served for this organization: nothing to list.
                return [], True
            denied.append(workspace["id"])
            continue
        if denied:
            logger.debug(
                "LangSmith %s was denied in %d workspace(s) before one answered",
                path,
                len(denied),
            )
        return rows, True
    if workspaces:
        logger.warning(
            "Skipping LangSmith %s: no workspace allowed it; the credential needs "
            "deployments:read in at least one workspace.",
            path,
        )
    return [], not workspaces


@timeit
def get_connections(
    client: LangSmithClient,
    org_id: str,
    agents: list[dict[str, Any]],
    workspace_by_deployment: dict[str, str],
) -> tuple[list[dict[str, Any]], set[str], bool]:
    """
    Fetch each agent's OAuth connections.

    This route takes the agent from the path rather than from the caller's identity, so it
    gives the organization-wide view of which agent holds which user's token. It is
    workspace-scoped, so each agent is queried in the workspaces of the deployments that
    serve it.

    Returns the connections, the graph ids of the agents whose connections were read in
    every one of their workspaces, and whether every listing answered.
    """
    connections: dict[str, dict[str, Any]] = {}
    read_agent_ids: set[str] = set()
    complete = True
    for agent in agents:
        # The API is keyed by the raw assistant id; agent["id"] is namespaced by
        # organization for the graph and is not a valid path segment here.
        assistant_id = agent["assistant_id"]
        workspace_ids = sorted(
            {
                workspace_by_deployment[deployment_id]
                for deployment_id in agent.get("deployment_ids") or []
                if deployment_id in workspace_by_deployment
            }
        )
        agent_read = bool(workspace_ids)
        for workspace_id in workspace_ids:
            try:
                payload = client.get(
                    f"/v2/auth/agents/{assistant_id}/connections",
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
                        assistant_id,
                        workspace_id,
                        err,
                    )
                    complete = False
                    agent_read = False
                continue
            for row in payload.get("data") or []:
                connections.setdefault(row["id"], row)
        if agent_read:
            read_agent_ids.add(agent["id"])
    return list(connections.values()), read_agent_ids, complete


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
                # Namespaced to match the agent node, which is namespaced because
                # LangSmith derives assistant ids from graphs and they can repeat across
                # organizations.
                "agent_id": (
                    f"{org_id}|{connection['agent_id']}"
                    if connection.get("agent_id")
                    else None
                ),
                "assistant_id": connection.get("agent_id"),
                "provider_id": connection.get("provider_id"),
                "provider_uuid": (
                    provider_uuid_by_slug.get(connection["provider_id"])
                    if connection.get("provider_id")
                    else None
                ),
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
    """Create agent records for agents named by a credential but not seen on a deployment."""
    known = {agent["id"] for agent in known_agents}
    extra: dict[str, dict[str, Any]] = {}
    for credential in credentials:
        agent_id = credential.get("agent_id")
        if not agent_id or agent_id in known or agent_id in extra:
            continue
        extra[agent_id] = {
            "id": agent_id,
            "assistant_id": credential.get("assistant_id"),
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
    load(
        neo4j_session,
        LangSmithAgentSchema(),
        agents,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load(
        neo4j_session,
        LangSmithOAuthProviderSchema(),
        providers,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load(
        neo4j_session,
        LangSmithAgentCredentialSchema(),
        credentials,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
