import logging
import threading
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

# LangSmith's member endpoints cap `limit` at 500. Deployments cap it at 100.
_MEMBER_PAGE_SIZE = 500
_DEPLOYMENT_PAGE_SIZE = 100
# Assistant searches run concurrently across deployments, so one scaled-to-zero
# deployment waking slowly no longer holds up the rest. That makes a tighter read
# timeout safe, and it bounds the worst case for a workspace full of idle deployments.
_ASSISTANT_TIMEOUT = (5, 15)
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


def _build_assistant_session() -> requests.Session:
    """
    Build a session for the read-only assistant search, which is expressed as a POST.

    Throttling and transient 5xx responses are retried, but read timeouts are not: a
    scaled-to-zero deployment that times out once will time out again, and retrying it
    would multiply the worst case the tight timeout exists to bound.
    """
    session = requests.Session()
    retry_policy = Retry(
        total=3,
        read=0,
        backoff_factor=1,
        status_forcelist=_RETRY_STATUSES,
        allowed_methods=["POST"],
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
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
            session = _build_assistant_session()
            self._thread_local.session = session
        return session

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

    def search_assistants(
        self,
        deployment_url: str,
        tenant_id: str,
        page_size: int = 100,
    ) -> tuple[list[dict[str, Any]], bool]:
        """
        List the assistants (agents) served by one deployment.

        LangSmith agent ids are assistant ids, and they live on each deployment's own data
        plane rather than in the control plane. This is the only way to enumerate them, and
        it is what makes the agent-to-user OAuth graph reachable.

        Expressed as a POST because /assistants/search is a search; it reads and never
        mutates. The deployment API key check is tenant-scoped, so X-Tenant-Id is required:
        without it the data plane answers 403 "API key tenant mismatch".

        Returns the assistants and whether the listing completed. A failure must not be
        reported as an empty inventory, because callers use that inventory to decide what
        to delete.

        Redirects are refused. The deployment host comes from API data rather than from
        operator configuration, and requests only strips the Authorization header when a
        redirect changes host — a custom header like X-Api-Key would be forwarded intact,
        handing an organization-admin token to whatever the redirect names.
        """
        if not deployment_url.lower().startswith("https://"):
            logger.warning(
                "Refusing to send credentials to non-HTTPS deployment URL for tenant %s",
                tenant_id,
            )
            return [], False

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
                    allow_redirects=False,
                )
            except requests.RequestException as err:
                logger.warning("Assistant search failed for a deployment: %s", err)
                return assistants, False
            if response.is_redirect or response.is_permanent_redirect:
                logger.warning(
                    "Refusing to follow a redirect from a deployment's assistant search "
                    "(status %s): following it would forward the API key to another host.",
                    response.status_code,
                )
                return assistants, False
            if response.status_code != 200:
                logger.warning(
                    "Assistant search returned %s for a deployment",
                    response.status_code,
                )
                return assistants, False
            page = response.json()
            if not isinstance(page, list):
                logger.warning(
                    "Assistant search returned an unexpected shape for a deployment"
                )
                return assistants, False
            assistants.extend(page)
            if len(page) < page_size:
                return assistants, True
            offset += len(page)


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
