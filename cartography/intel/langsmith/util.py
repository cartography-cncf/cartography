import logging
import threading
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)

# Connect and read timeouts of 60 seconds each; see
# https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)

# LangSmith's member endpoints cap `limit` at 500. Deployments cap it at 100.
_MEMBER_PAGE_SIZE = 500
_DEPLOYMENT_PAGE_SIZE = 100
_CURSOR_PAGE_SIZE = 100
# Assistant searches run concurrently across deployments, so one scaled-to-zero
# deployment waking slowly no longer holds up the rest. That makes a tighter read
# timeout safe, and it bounds the worst case for a workspace full of idle deployments.
_ASSISTANT_TIMEOUT = (5, 15)


def _build_session() -> requests.Session:
    """Build a session with the shared retry policy."""
    session = requests.Session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        # LangSmith signals throttling with Retry-After and emits no X-RateLimit headers.
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.mount("http://", HTTPAdapter(max_retries=retry_policy))
    return session


class LangSmithPermissionError(Exception):
    """Raised when the configured credential cannot read a LangSmith resource."""


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
        self._thread_local = threading.local()

    @property
    def _worker_session(self) -> requests.Session:
        """
        A session private to the calling thread.

        requests.Session is not guaranteed thread-safe, and assistant searches run on a
        thread pool, so each worker gets its own rather than sharing the client's.
        """
        session = getattr(self._thread_local, "session", None)
        if session is None:
            session = _build_session()
            self._thread_local.session = session
        return session

    def _headers(
        self,
        org_id: str | None,
        tenant_id: str | None,
        bearer: bool,
    ) -> dict[str, str]:
        # Two tenantless routes (/api/v1/orgs and /api/v1/orgs/permissions) only accept a
        # bearer token; everything else takes the same PAT as an API key.
        if bearer:
            headers = {"Authorization": f"Bearer {self._pat}"}
        else:
            headers = {"X-Api-Key": self._pat}
        if org_id:
            headers["X-Organization-Id"] = org_id
        if tenant_id:
            headers["X-Tenant-Id"] = tenant_id
        return headers

    def _request(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        org_id: str | None = None,
        tenant_id: str | None = None,
        bearer: bool = False,
        host: bool = False,
    ) -> Any:
        base = self.host_api_url if host else self.api_url
        response = self._session.get(
            f"{base}{path}",
            params=params,
            headers=self._headers(org_id, tenant_id, bearer),
            timeout=_TIMEOUT,
        )
        if response.status_code in (401, 403, 404):
            raise LangSmithPermissionError(
                f"GET {path} returned {response.status_code}: "
                f"the configured LangSmith credential cannot read this resource."
            )
        response.raise_for_status()
        return response.json()

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        org_id: str | None = None,
        tenant_id: str | None = None,
        bearer: bool = False,
        host: bool = False,
    ) -> Any:
        """Fetch a single, unpaginated LangSmith response and return it as-is."""
        return self._request(
            path,
            params=params,
            org_id=org_id,
            tenant_id=tenant_id,
            bearer=bearer,
            host=host,
        )

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
            page = self._request(
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
            payload = self._request(
                path,
                params=page_params,
                org_id=org_id,
                tenant_id=tenant_id,
                host=host,
            )
            page = payload.get(key) or []
            results.extend(page)
            if len(page) < page_size:
                return results
            offset += len(page)

    def get_paginated_cursor(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        org_id: str | None = None,
        tenant_id: str | None = None,
        page_size: int = _CURSOR_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        """
        Page through a cursor-paginated endpoint returning ``{"items": [...],
        "next_cursor": ...}``. This is the newer house convention used by the Go
        agent-auth routes.
        """
        results: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            page_params = dict(params or {})
            page_params["page_size"] = page_size
            if cursor:
                page_params["after_id"] = cursor
            payload = self._request(
                path,
                params=page_params,
                org_id=org_id,
                tenant_id=tenant_id,
            )
            # Some of these routes return a bare array rather than an envelope.
            if isinstance(payload, list):
                return results + payload
            results.extend(payload.get("items") or [])
            cursor = payload.get("next_cursor")
            if not cursor:
                return results

    def search_assistants(
        self,
        deployment_url: str,
        tenant_id: str,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List the assistants (agents) served by one deployment.

        LangGraph Platform agent ids are assistant ids, and they live on each deployment's
        own data plane rather than in the control plane. This is the only way to enumerate
        them, and it is what makes the agent-to-user OAuth graph reachable.

        Expressed as a POST because /assistants/search is a search; it reads and never
        mutates. The deployment API key check is tenant-scoped, so X-Tenant-Id is
        required: without it the data plane answers 403 "API key tenant mismatch".

        Deployments can be scaled to zero and take longer than a normal request to wake,
        and some reject the credential outright, so every failure here degrades to an
        empty list rather than breaking the sync.
        """
        assistants: list[dict[str, Any]] = []
        offset = 0
        url = deployment_url.rstrip("/") + "/assistants/search"
        headers = {"X-Api-Key": self._pat, "X-Tenant-Id": tenant_id}
        while True:
            try:
                response = self._worker_session.post(
                    url,
                    json={"limit": page_size, "offset": offset},
                    headers=headers,
                    timeout=_ASSISTANT_TIMEOUT,
                )
            except requests.RequestException as err:
                logger.debug("Assistant search failed for a deployment: %s", err)
                return assistants
            if response.status_code != 200:
                logger.debug(
                    "Assistant search returned %s for a deployment",
                    response.status_code,
                )
                return assistants
            page = response.json()
            if not isinstance(page, list):
                return assistants
            assistants.extend(page)
            if len(page) < page_size:
                return assistants
            offset += len(page)


def build_user_lookup(users: list[dict[str, Any]]) -> dict[str, str]:
    """
    Build a tolerant lookup from whatever a created_by/owner_id field might hold to a stable
    ls_user_id.

    LangSmith does not document whether these fields carry an ls_user_id, an identity UUID or
    an email address, and the answer differs between the control plane and the two agent-auth
    subsystems. Every identifier we know for a user therefore maps back to its ls_user_id.
    """
    lookup: dict[str, str] = {}
    for user in users:
        ls_user_id = user["ls_user_id"]
        lookup[ls_user_id] = ls_user_id
        if user.get("org_identity_id"):
            lookup[user["org_identity_id"]] = ls_user_id
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
