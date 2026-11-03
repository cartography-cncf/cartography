import copy
from typing import Any

from cartography.intel.langsmith.util import LangSmithFetchError
from tests.data.langsmith import agent_auth
from tests.data.langsmith import apikeys
from tests.data.langsmith import deployments
from tests.data.langsmith import organizations
from tests.data.langsmith import roles
from tests.data.langsmith import users
from tests.data.langsmith import workspace_resources
from tests.data.langsmith.workspaces import LANGSMITH_WORKSPACES
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID

Route = tuple[str, str | None]

WORKSPACE_IDS = (WORKSPACE_PROD_ID, WORKSPACE_DEV_ID)


def _per_workspace(path: str, payloads: dict[str, Any]) -> dict[Route, Any]:
    return {
        (path, workspace_id): payloads[workspace_id] for workspace_id in WORKSPACE_IDS
    }


def _same_in_every_workspace(path: str, payload: Any) -> dict[Route, Any]:
    return {(path, workspace_id): payload for workspace_id in WORKSPACE_IDS}


TAG_KEY_ID = workspace_resources.LANGSMITH_TAG_KEYS[WORKSPACE_PROD_ID][0]["id"]

# What the LangSmith API answers for the Simpson Corp organization, keyed by
# (path, X-Tenant-Id). Paginated listings are stored already unwrapped, the way the real
# client returns them.
SIMPSON_CORP_ROUTES: dict[Route, Any] = {
    ("/api/v1/workspaces", None): LANGSMITH_WORKSPACES,
    ("/api/v1/orgs/current/info", None): organizations.LANGSMITH_ORG_INFO,
    ("/api/v1/orgs/current/roles", None): roles.LANGSMITH_ROLES,
    ("/api/v1/orgs/current/members/active", None): users.LANGSMITH_ACTIVE_ORG_MEMBERS,
    ("/api/v1/orgs/current/members/pending", None): users.LANGSMITH_PENDING_ORG_MEMBERS,
    **_per_workspace(
        "/api/v1/workspaces/current/members", users.LANGSMITH_WORKSPACE_MEMBERS
    ),
    ("/api/v1/service-accounts", None): apikeys.LANGSMITH_SERVICE_ACCOUNTS,
    ("/api/v1/orgs/current/service-keys", None): apikeys.LANGSMITH_SERVICE_KEYS,
    (
        "/api/v1/orgs/current/members/personal-access-tokens",
        None,
    ): apikeys.LANGSMITH_PATS,
    ("/api/v1/platform/orgs/current/scim/tokens", None): apikeys.LANGSMITH_SCIM_TOKENS,
    **_per_workspace("/api/v1/api-key", apikeys.LANGSMITH_WORKSPACE_KEYS),
    (
        "/api/v1/orgs/current/sso-settings",
        None,
    ): workspace_resources.LANGSMITH_SSO_SETTINGS,
    (
        "/api/v1/platform/orgs/current/access-policies",
        None,
    ): workspace_resources.LANGSMITH_ACCESS_POLICIES,
    ("/orgs/current/data-planes", None): workspace_resources.LANGSMITH_DATA_PLANES,
    **_per_workspace("/v2/deployments", deployments.LANGSMITH_DEPLOYMENTS),
    **_same_in_every_workspace(
        "/v2/auth/providers", agent_auth.LANGSMITH_OAUTH_PROVIDERS
    ),
    **_same_in_every_workspace("/v2/auth/platform-providers", []),
    (
        f"/v2/auth/agents/{deployments.SUPPORT_AGENT_ID}/connections",
        WORKSPACE_PROD_ID,
    ): agent_auth.LANGSMITH_AGENT_CONNECTIONS[deployments.SUPPORT_AGENT_ID],
    (
        f"/v2/auth/agents/{deployments.TRIAGE_AGENT_ID}/connections",
        WORKSPACE_DEV_ID,
    ): agent_auth.LANGSMITH_AGENT_CONNECTIONS[deployments.TRIAGE_AGENT_ID],
    **_per_workspace(
        "/api/v1/workspaces/current/secrets", workspace_resources.LANGSMITH_SECRETS
    ),
    **_per_workspace(
        "/api/v1/workspaces/current/tag-keys", workspace_resources.LANGSMITH_TAG_KEYS
    ),
    (
        f"/api/v1/workspaces/current/tag-keys/{TAG_KEY_ID}/tag-values",
        WORKSPACE_PROD_ID,
    ): workspace_resources.LANGSMITH_TAG_VALUES[TAG_KEY_ID],
    **_per_workspace(
        "/api/v1/platform/oauth/clients", workspace_resources.LANGSMITH_OAUTH_CLIENTS
    ),
    **_per_workspace(
        "/api/v1/platform/mcp-vendors", workspace_resources.LANGSMITH_MCP_VENDORS
    ),
    (
        "/api/v1/platform/mcp-vendors/arcade/mcp-servers",
        WORKSPACE_PROD_ID,
    ): workspace_resources.LANGSMITH_MCP_SERVERS["arcade"],
}


class FakeLangSmithClient:
    """
    Stands in for LangSmithClient at the HTTP boundary.

    Unknown routes answer 404, as the real API does. Routes in ``failures`` fail with the
    given status, or with a timeout when the status is None, the way the real client
    reports them. Deployments in ``cold_deployment_urls`` fail their assistant search,
    the way a scaled-to-zero deployment times out.
    """

    def __init__(
        self,
        routes: dict[Route, Any] | None = None,
        failures: dict[Route, int | None] | None = None,
        cold_deployment_urls: frozenset[str] = frozenset(),
    ) -> None:
        self.routes = SIMPSON_CORP_ROUTES if routes is None else routes
        self.failures = failures or {}
        self.cold_deployment_urls = cold_deployment_urls

    def get(self, path: str, *, tenant_id: str | None = None, **_: Any) -> Any:
        route = (path, tenant_id)
        if route in self.failures:
            status = self.failures[route]
            raise LangSmithFetchError(path, status, f"HTTP {status or 'timeout'}")
        if route not in self.routes:
            raise LangSmithFetchError(path, 404, "HTTP 404")
        # Callers annotate the rows they receive, so hand out copies.
        return copy.deepcopy(self.routes[route])

    get_paginated = get
    get_paginated_envelope = get

    def search_assistants(
        self, deployment_url: str, tenant_id: str
    ) -> tuple[list[dict[str, Any]], bool]:
        if deployment_url in self.cold_deployment_urls:
            return [], False
        return (
            copy.deepcopy(deployments.LANGSMITH_ASSISTANTS.get(deployment_url, [])),
            True,
        )
