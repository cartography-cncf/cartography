import logging
import time
from datetime import datetime
from datetime import timezone
from typing import Any

import neo4j
import requests
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)


def epoch_ms_to_datetime(value: Any) -> datetime | None:
    """Convert Databricks epoch-milliseconds timestamps to a UTC datetime."""
    if value in (None, 0):
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)


def iso_to_datetime(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp (as the SQL / Lakeview APIs return) to datetime.

    Unlike the older endpoints (epoch milliseconds), the SQL and Lakeview APIs
    return RFC-3339 strings such as ``2026-07-01T23:27:40Z``; ``isoparse``
    handles the trailing ``Z`` and offset forms, matching the rest of the repo.
    """
    if not value:
        return None
    return dateutil_parser.isoparse(str(value))


def get_run_as_principal_index(
    neo4j_session: neo4j.Session, workspace_id: str
) -> dict[str, tuple[str, bool]]:
    """Map a run-as principal name to ``(scoped node id, is_service_principal)``.

    Jobs and pipelines report their run-as identity by name (a user's
    ``user_name`` or a service principal's ``application_id``). Resolving that
    against *this workspace's* principals keeps a name shared across workspaces
    (federated identities routinely share an email) from attaching the RUN_AS
    edge to the wrong principal node. Mirrors ``grants.get_principals`` but
    keeps the user/service-principal distinction the RUN_AS edge needs.
    """
    query = """
    MATCH (:DatabricksWorkspace {id: $workspace_id})-[:RESOURCE]->(p)
    WHERE p:DatabricksUser OR p:DatabricksServicePrincipal
    RETURN p.id AS id,
           p:DatabricksServicePrincipal AS is_sp,
           CASE
               WHEN p:DatabricksServicePrincipal THEN p.application_id
               ELSE p.user_name
           END AS name
    """
    result = neo4j_session.run(query, workspace_id=workspace_id)
    index: dict[str, tuple[str, bool]] = {}
    for record in result:
        if record["name"] and record["id"]:
            index[record["name"]] = (record["id"], bool(record["is_sp"]))
    return index


def uc_id(metastore_id: str, full_name: str) -> str:
    """Build a metastore-scoped id for a Unity Catalog securable.

    UC full names (``catalog``, ``catalog.schema``, ``catalog.schema.table``)
    are unique within a metastore, so ``{metastore_id}/{full_name}`` is a stable
    key that children can recompute from their parent's full name.

    Both parts must be non-empty: a blank metastore id would collapse securables
    from different metastores onto the same node.
    """
    if not metastore_id or not full_name:
        raise ValueError(
            f"Cannot build a Unity Catalog id from metastore_id="
            f"{metastore_id!r}, full_name={full_name!r}",
        )
    return f"{metastore_id}/{full_name}"


def skip_or_raise_http(error: requests.HTTPError, *skippable_statuses: int) -> None:
    """Re-raise an HTTP error unless its status is an expected, skippable one.

    Unity Catalog listings are fetched per parent (per catalog / schema / ...).
    A ``403`` on a system-managed securable is expected and skippable, but a
    transient ``5x`` or an auth failure must abort the sync so the caller does
    NOT run cleanup on partial data and delete still-valid nodes.
    """
    status = error.response.status_code if error.response is not None else None
    if status not in skippable_statuses:
        raise error


# Connect and read timeouts of 60 seconds each.
_TIMEOUT = (60, 60)
_SCIM_PAGE_SIZE = 100


def scoped_id(workspace_id: str, scim_id: str) -> str:
    """Build a workspace-scoped node id ``{workspace_id}/{scim_id}``.

    Databricks SCIM ids are workspace-scoped, not globally unique, so node ids
    must include the workspace to keep multi-workspace ingestion from collapsing
    same-id principals into a single Neo4j node.
    """
    return f"{workspace_id}/{scim_id}"


class _BaseDatabricksClient:
    """Shared REST plumbing for the Databricks workspace + account APIs.

    Both APIs speak the same request/response shapes (SCIM listings, Unity
    Catalog ``next_page_token`` pagination, bearer auth). They differ only in the
    OAuth token endpoint (``_token_url``), so that is the single override point.

    Supports two authentication modes:
      - Personal Access Token (PAT): pass ``token`` (workspace API only).
      - OAuth M2M (service principal client credentials): pass ``client_id`` and
        ``client_secret``.
    """

    def __init__(
        self,
        host: str,
        token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        if not token and not (client_id and client_secret):
            raise ValueError(
                "Must provide either token, or both client_id and client_secret.",
            )
        self.host = host.rstrip("/")
        self._token = token
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token_expiry: float | None = None
        self._session = requests.Session()

    def _token_url(self) -> str:
        raise NotImplementedError

    def authenticate(self) -> None:
        if self._token:
            self._session.headers["Authorization"] = f"Bearer {self._token}"
            return
        if self._access_token_expiry and self._access_token_expiry >= time.time():
            return
        self._session.headers.pop("Authorization", None)
        response = self._session.post(
            self._token_url(),
            data={"grant_type": "client_credentials", "scope": "all-apis"},
            auth=(self._client_id, self._client_secret),  # type: ignore[arg-type]
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        self._session.headers["Authorization"] = f"Bearer {data['access_token']}"
        self._access_token_expiry = time.time() + data.get("expires_in", 0)
        logger.debug(
            "Databricks access token renewed, expires in %s seconds.",
            data.get("expires_in", 0),
        )

    def get(self, uri: str, params: dict | None = None) -> Any:
        """Single GET that returns the parsed JSON body."""
        self.authenticate()
        response = self._session.get(
            f"{self.host}{uri}",
            params=params or {},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def scim_list(self, uri: str) -> list[dict[str, Any]]:
        """Paginate a SCIM listing endpoint and return all resources."""
        results: list[dict[str, Any]] = []
        start_index = 1
        while True:
            data = self.get(
                uri,
                params={"startIndex": start_index, "count": _SCIM_PAGE_SIZE},
            )
            resources = data.get("Resources", []) or []
            results.extend(resources)
            total = int(data.get("totalResults", 0))
            if not resources or start_index + len(resources) - 1 >= total:
                break
            start_index += len(resources)
        return results

    def uc_list(
        self, uri: str, key: str, params: dict | None = None
    ) -> list[dict[str, Any]]:
        """Paginate a Unity Catalog listing endpoint (``next_page_token``).

        UC list endpoints return the resources under ``key`` and a
        ``next_page_token`` to fetch the next page; an empty/absent token ends
        the walk.
        """
        results: list[dict[str, Any]] = []
        page_params = {**(params or {})}
        seen_tokens: set[str] = set()
        while True:
            data = self.get(uri, params=page_params)
            results.extend(data.get(key, []) or [])
            next_token = data.get("next_page_token")
            if not next_token:
                break
            # Guard against a malformed response that keeps returning the same
            # token, which would otherwise loop forever.
            if next_token in seen_tokens:
                raise ValueError(
                    f"Unity Catalog listing {uri} repeated page token "
                    f"{next_token!r}; aborting to avoid an infinite loop.",
                )
            seen_tokens.add(next_token)
            page_params = {**(params or {}), "page_token": next_token}
        return results


class DatabricksWorkspaceClient(_BaseDatabricksClient):
    """A thin client for the Databricks Workspace REST API."""

    def _token_url(self) -> str:
        return f"{self.host}/oidc/v1/token"


class DatabricksAccountClient(_BaseDatabricksClient):
    """A thin client for the Databricks Account REST API.

    The account API lives on a different host (``accounts.cloud.databricks.com``
    on AWS, ``accounts.gcp.databricks.com`` on GCP; Azure has no account API) and
    the OAuth token endpoint is account-scoped. Every account resource path is
    prefixed with ``/api/2.0/accounts/{account_id}``, so callers build URIs with
    :attr:`account_id`. OAuth M2M is the only supported auth (no PAT).
    """

    def __init__(
        self,
        host: str,
        account_id: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        super().__init__(host, client_id=client_id, client_secret=client_secret)
        self.account_id = account_id

    def _token_url(self) -> str:
        return f"{self.host}/oidc/accounts/{self.account_id}/v1/token"

    def account_uri(self, suffix: str) -> str:
        """Build an account-scoped API path from a suffix like ``/scim/v2/Users``."""
        return f"/api/2.0/accounts/{self.account_id}{suffix}"


def parse_storage_url(url: str | None) -> tuple[str | None, str | None]:
    """Return ``(scheme, bucket)`` for a UC storage URL, else ``(None, None)``.

    Handles ``s3://bucket/path`` and ``gs://bucket/path`` (bucket is the netloc)
    and ``abfss://container@account.dfs.core.windows.net/path`` (container is the
    netloc user-info). Used to link tables / volumes / external locations to the
    underlying S3 / GCS bucket already ingested by the aws / gcp modules.
    """
    if not url:
        return None, None
    scheme, _, rest = url.partition("://")
    if not rest:
        return None, None
    netloc = rest.split("/", 1)[0]
    if scheme.lower() in ("abfss", "abfs", "wasbs", "wasb"):
        # container@account.dfs.core.windows.net -> container
        return scheme.lower(), (netloc.split("@", 1)[0] or None)
    return scheme.lower(), (netloc or None)
