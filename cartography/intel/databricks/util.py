import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

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


class DatabricksWorkspaceClient:
    """A thin client for the Databricks Workspace REST API.

    Supports two authentication modes:
      - Personal Access Token (PAT): pass ``token``.
      - OAuth M2M (workspace-level service principal client credentials):
        pass ``client_id`` and ``client_secret``.
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

    def authenticate(self) -> None:
        if self._token:
            self._session.headers["Authorization"] = f"Bearer {self._token}"
            return
        if self._access_token_expiry and self._access_token_expiry >= time.time():
            return
        self._session.headers.pop("Authorization", None)
        response = self._session.post(
            f"{self.host}/oidc/v1/token",
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
