import logging
from typing import Any

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.graph.job import GraphJob
from cartography.models.core.nodes import CartographyNodeSchema

logger = logging.getLogger(__name__)

# Connect and read timeouts of 60 seconds each; see
# https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)

# LangSmith's member endpoints cap `limit` at 500. Deployments cap it at 100, and so do
# the cursor-paginated registries.
_MEMBER_PAGE_SIZE = 500
_DEPLOYMENT_PAGE_SIZE = 100
_CURSOR_PAGE_SIZE = 100
_RETRY_STATUSES = [429, 500, 502, 503, 504]


def _build_session() -> requests.Session:
    """Build a session with the shared retry policy."""
    session = requests.Session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=_RETRY_STATUSES,
        allowed_methods=["GET"],
        # LangSmith signals throttling with Retry-After and emits no X-RateLimit headers.
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.mount("http://", HTTPAdapter(max_retries=retry_policy))
    return session


class LangSmithFetchError(Exception):
    """Raised when a LangSmith listing could not be read in full."""

    def __init__(self, path: str, status_code: int | None, reason: str) -> None:
        super().__init__(f"GET {path} failed: {reason}")
        self.status_code = status_code

    @property
    def not_found(self) -> bool:
        # A 404 means the route or resource does not exist for this organization, which
        # is a complete (empty) answer. A 401/403 or a transport failure means data may
        # exist that we could not see, so callers must not treat it as an empty inventory.
        return self.status_code == 404


class LangSmithClient:
    """
    A client for the LangSmith REST API.

    LangSmith spreads its read surface over two hosts: the control plane
    (organizations, workspaces, identities, roles, keys) and the LangGraph Platform
    "api-host" (deployments and agent OAuth connections). This client talks to both and
    assembles the scope headers each route needs.

    Scope is selected per request: organization routes take ``X-Organization-Id`` and
    workspace routes take ``X-Tenant-Id``. Sending a workspace route without a tenant
    header returns 403.
    """

    def __init__(self, pat: str, api_url: str, host_api_url: str) -> None:
        self._pat = pat
        self.api_url = api_url.rstrip("/")
        self.host_api_url = host_api_url.rstrip("/")
        self._session = _build_session()

    def _headers(self, org_id: str | None, tenant_id: str | None) -> dict[str, str]:
        headers = {"X-Api-Key": self._pat}
        if org_id:
            headers["X-Organization-Id"] = org_id
        if tenant_id:
            headers["X-Tenant-Id"] = tenant_id
        return headers

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        org_id: str | None = None,
        tenant_id: str | None = None,
        host: bool = False,
    ) -> Any:
        """Fetch a single, unpaginated LangSmith response and return it as-is."""
        base = self.host_api_url if host else self.api_url
        try:
            response = self._session.get(
                f"{base}{path}",
                params=params,
                headers=self._headers(org_id, tenant_id),
                timeout=_TIMEOUT,
            )
        except requests.RequestException as err:
            # Timeouts, connection failures and exhausted 429/5xx retries. Reported like
            # a denied listing so the caller preserves existing nodes instead of failing
            # the whole sync or deleting them.
            raise LangSmithFetchError(path, None, type(err).__name__) from err
        if response.status_code in (401, 403, 404):
            raise LangSmithFetchError(
                path, response.status_code, f"HTTP {response.status_code}"
            )
        response.raise_for_status()
        return response.json()

    def get_paginated(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        org_id: str | None = None,
        tenant_id: str | None = None,
        page_size: int = _MEMBER_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        """
        Page through an endpoint that takes limit/offset and returns a bare JSON array.

        This covers the member listings, which report their total in the
        ``X-Pagination-Total`` response header rather than in the body. We page until a
        short page comes back, so the header is not needed.
        """
        results: list[dict[str, Any]] = []
        offset = 0
        while True:
            page_params = dict(params or {})
            page_params.update({"limit": page_size, "offset": offset})
            page = self.get(
                path,
                params=page_params,
                org_id=org_id,
                tenant_id=tenant_id,
            )
            results.extend(page)
            if len(page) < page_size:
                return results
            offset += len(page)

    def get_paginated_envelope(
        self,
        path: str,
        *,
        key: str,
        params: dict[str, Any] | None = None,
        org_id: str | None = None,
        tenant_id: str | None = None,
        page_size: int = _DEPLOYMENT_PAGE_SIZE,
        host: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Page through an endpoint that takes limit/offset and wraps its rows in an envelope,
        for example the deployments listing's ``{"resources": [...], "offset": N}``.
        """
        results: list[dict[str, Any]] = []
        offset = 0
        while True:
            page_params = dict(params or {})
            page_params.update({"limit": page_size, "offset": offset})
            payload = self.get(
                path,
                params=page_params,
                org_id=org_id,
                tenant_id=tenant_id,
                host=host,
            )
            # Indexed rather than defaulted: a response missing its rows must fail loudly,
            # not read as an empty inventory that cleanup would then act on.
            page = payload[key]
            results.extend(page)
            if len(page) < page_size:
                return results
            offset += len(page)

    def get_cursor_paginated(
        self,
        path: str,
        *,
        key: str,
        org_id: str | None = None,
        tenant_id: str | None = None,
        page_size: int = _CURSOR_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        """
        Page through an endpoint that takes page_size/cursor and wraps its rows in an
        envelope with a ``next_cursor``, for example the agent registry's
        ``{"items": [...], "next_cursor": "..."}``.
        """
        results: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": page_size}
            if cursor:
                params["cursor"] = cursor
            payload = self.get(path, params=params, org_id=org_id, tenant_id=tenant_id)
            # Indexed rather than defaulted, for the same reason as the offset envelope.
            results.extend(payload[key])
            cursor = payload.get("next_cursor")
            if not cursor:
                return results


def org_scoped_id(org_id: str, raw_id: str | None) -> str | None:
    """
    Namespace an id LangSmith reuses across organizations, such as a built-in role's.

    Nodes keyed on such an id would otherwise be shared between organizations, and one
    organization's cleanup would prune the other's relationships on them.
    """
    return f"{org_id}|{raw_id}" if raw_id else None


def build_user_lookup(
    users: list[dict[str, Any]], org_memberships: list[dict[str, Any]]
) -> dict[str, str]:
    """
    Build a tolerant lookup from whatever a created_by/owner_id field might hold to a stable
    ls_user_id.

    LangSmith does not document whether these fields carry an ls_user_id, an identity UUID or
    an email address, and the answer differs between the control plane and the two agent-auth
    subsystems. Every identifier we know for a user therefore maps back to its ls_user_id.
    Identity UUIDs are per organization, so they come from the organization memberships.
    """
    lookup: dict[str, str] = {}
    for membership in org_memberships:
        if membership.get("identity_id"):
            lookup[membership["identity_id"]] = membership["ls_user_id"]
    for user in users:
        ls_user_id = user["ls_user_id"]
        lookup[ls_user_id] = ls_user_id
        if user.get("email"):
            lookup[user["email"].lower()] = ls_user_id
        # created_by on the key endpoints is frequently a bare username rather than an id
        # or an email, so index those too.
        for username in user.get("usernames") or []:
            lookup.setdefault(username.lower(), ls_user_id)
    return lookup


def resolve_ls_user_id(candidate: str | None, lookup: dict[str, str]) -> str | None:
    """Resolve an opaque user reference to a stable ls_user_id, or None if unrecognized."""
    if not candidate:
        return None
    return lookup.get(candidate) or lookup.get(str(candidate).lower())


def cleanup_if_complete(
    neo4j_session: neo4j.Session,
    schema: CartographyNodeSchema,
    complete: bool,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Run a schema's cleanup only when the collection that fed it completed.

    Deleting on a partial collection would erase nodes that still exist in a workspace or
    listing the credential could not read. Stale nodes are the lesser harm.
    """
    if not complete:
        logger.warning(
            "Skipping %s cleanup for LangSmith organization %s: collection was incomplete, "
            "so existing nodes are preserved rather than deleted.",
            schema.label,
            common_job_parameters["ORG_ID"],
        )
        return
    GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)
