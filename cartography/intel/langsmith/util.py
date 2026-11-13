import logging
import threading
from typing import Any

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.graph.cleanupbuilder import build_cleanup_queries
from cartography.graph.job import GraphJob
from cartography.graph.statement import GraphStatement
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

    Throttling and transient 5xx responses are retried, but connect and read timeouts
    are not: a scaled-to-zero or unreachable deployment that times out once will time out
    again, and retrying it would multiply the worst case the tight timeout exists to
    bound. A failed listing only defers agent cleanup, so giving up early is safe.
    """
    session = requests.Session()
    retry_policy = Retry(
        total=3,
        connect=0,
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
    ) -> tuple[list[dict[str, Any]], str | None]:
        """
        List the assistants (agents) served by one deployment.

        LangSmith agent ids are assistant ids, and they live on each deployment's own data
        plane rather than in the control plane. This is the only way to enumerate them, and
        it is what makes the agent-to-user OAuth graph reachable.

        Expressed as a POST because /assistants/search is a search; it reads and never
        mutates. The deployment API key check is tenant-scoped, so X-Tenant-Id is required:
        without it the data plane answers 403 "Invalid tenant ID".

        Returns the assistants and, when the listing did not complete, a short reason such
        as ``HTTP 401`` or an exception class name (``None`` means it completed). A failure
        must not be reported as an empty inventory, because callers use that inventory to
        decide what to delete. Per-deployment failures are logged at DEBUG; the caller
        reports them in aggregate, since one organization can have hundreds.

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
            return [], "non-HTTPS URL"

        assistants: list[dict[str, Any]] = []
        offset = 0
        url = deployment_url.rstrip("/") + "/assistants/search"
        headers = {
            "X-Api-Key": self._pat,
            "X-Tenant-Id": tenant_id,
            # A deployment with custom auth hands every request to the customer's own
            # handler, which rejects a LangSmith key with 401. This header asks it to
            # route the key to LangSmith auth instead; deployments that disabled
            # LangSmith (studio) auth still refuse it.
            "x-auth-scheme": "langsmith",
        }
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
                logger.debug("Assistant search failed for %s: %s", url, err)
                return assistants, _request_failure_reason(err)
            if response.is_redirect or response.is_permanent_redirect:
                logger.warning(
                    "Refusing to follow a redirect from a deployment's assistant search "
                    "(status %s): following it would forward the API key to another host.",
                    response.status_code,
                )
                return assistants, "redirect"
            if response.status_code != 200:
                logger.debug(
                    "Assistant search returned %s for %s", response.status_code, url
                )
                return assistants, f"HTTP {response.status_code}"
            page = response.json()
            if not isinstance(page, list):
                logger.warning(
                    "Assistant search returned an unexpected shape for a deployment"
                )
                return assistants, "unexpected response shape"
            assistants.extend(page)
            if len(page) < page_size:
                return assistants, None
            offset += len(page)


def _request_failure_reason(err: requests.RequestException) -> str:
    """
    Name a transport failure by its root cause, without headers or the URL.

    requests wraps exhausted retries in ConnectionError or RetryError, so the class name
    alone would lump a connect timeout together with repeated 503s.
    """
    cause = err.args[0] if err.args else None
    reason = getattr(cause, "reason", None)
    if isinstance(reason, Exception):
        # urllib3's ResponseError means retryable statuses (429/5xx) never cleared.
        if type(reason).__name__ == "ResponseError":
            return "repeated 429/5xx"
        return type(reason).__name__
    return type(err).__name__


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


# A node is preserved when it hangs off a workspace that could not be read, or when it is
# an API key of a type whose organization-wide listing could not be read. Only the
# parameter values vary; the clause text is fixed.
_PRESERVE_UNREAD = (
    "EXISTS { MATCH (n)--(unread:LangSmithWorkspace) "
    "WHERE unread.id IN $LANGSMITH_UNREAD_WORKSPACE_IDS } "
    "OR n.key_type IN $LANGSMITH_UNREAD_KEY_TYPES"
)
_CLEANUP_ITERATION_SIZE = 10000


def cleanup_preserving_unread(
    neo4j_session: neo4j.Session,
    schema: CartographyNodeSchema,
    common_job_parameters: dict[str, Any],
    unread_workspace_ids: set[str],
    unread_key_types: set[str] | None = None,
) -> None:
    """
    Run a schema's cleanup everywhere its collection succeeded.

    A credential commonly cannot read one or two workspaces. Skipping cleanup outright
    would let stale nodes pile up in every other workspace as well, so instead the
    cleanup leaves alone only the nodes linked to a workspace (or, for API keys, of a key
    type) that could not be read, along with their relationships.

    The schema must be scoped to the organization through a relationship bound as ``s``,
    which every LangSmith node schema is.
    """
    unread_key_types = unread_key_types or set()
    if not unread_workspace_ids and not unread_key_types:
        GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)
        return

    logger.warning(
        "Cleaning up %s for LangSmith organization %s, but preserving nodes in %d "
        "workspace(s) that could not be read (%s)%s.",
        schema.label,
        common_job_parameters["ORG_ID"],
        len(unread_workspace_ids),
        ", ".join(sorted(unread_workspace_ids)) or "none",
        (
            f" and of key type(s) {', '.join(sorted(unread_key_types))}"
            if unread_key_types
            else ""
        ),
    )
    run_preserving_cleanup(
        neo4j_session,
        schema,
        common_job_parameters,
        _PRESERVE_UNREAD,
        {
            "LANGSMITH_UNREAD_WORKSPACE_IDS": sorted(unread_workspace_ids),
            "LANGSMITH_UNREAD_KEY_TYPES": sorted(unread_key_types),
        },
    )


def run_preserving_cleanup(
    neo4j_session: neo4j.Session,
    schema: CartographyNodeSchema,
    common_job_parameters: dict[str, Any],
    preserve_clause: str,
    preserve_parameters: dict[str, Any],
) -> None:
    """
    Run a schema's generated cleanup, leaving alone every node ``preserve_clause`` matches.

    ``preserve_clause`` is a Cypher boolean over the node ``n``. Callers pass a fixed
    module constant and supply every value it uses through ``preserve_parameters``, so
    no data from the API is ever interpolated into query text.
    """
    parameters = {**common_job_parameters, **preserve_parameters}
    statements = [
        GraphStatement(
            scope_cleanup_query(query, schema.label, preserve_clause),
            parameters=parameters,
            iterationsize=_CLEANUP_ITERATION_SIZE,
            batched_transactions=True,
            parent_job_name=schema.label,
            parent_job_sequence_num=idx,
        )
        for idx, query in enumerate(build_cleanup_queries(schema), start=1)
    ]
    GraphJob(f"Cleanup {schema.label}", statements, schema.label).run(neo4j_session)


def scope_cleanup_query(query: str, label: str, preserve_clause: str) -> str:
    """
    Narrow one generated cleanup query so it skips the nodes ``preserve_clause`` matches.

    Every query cartography generates for an organization-scoped schema opens by matching
    ``(n:<label>)`` and its organization edge ``s``. A filter on ``n`` is inserted right
    after that line, so it applies to both the stale-node and the stale-relationship
    statements. Anything else is refused rather than guessed at: a mis-scoped cleanup
    deletes data.
    """
    lines = query.strip().splitlines()
    first = lines[0].strip()
    if not first.startswith(f"MATCH (n:{label})") or "-[s:" not in first:
        raise ValueError(
            f"Unexpected cleanup query shape for {label}; refusing to scope it: {first!r}"
        )
    narrowed = [first, f"WITH n, s WHERE NOT ({preserve_clause})", "MATCH (n)"]
    return "\n".join(narrowed + lines[1:])
