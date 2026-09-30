import time
from dataclasses import dataclass
from dataclasses import field
from threading import Lock
from typing import Any
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.response import BaseHTTPResponse
from urllib3.util.retry import Retry

from cartography.util import DEFAULT_MAX_PAGES

TOKEN_URL = "https://zoom.us/oauth/token"
API_URL = "https://api.zoom.us/v2"
USERS_URL = f"{API_URL}/users"


DEFAULT_REQUEST_LIMIT = 100000


class ZoomRequestLimitError(RuntimeError):
    """The operator-configured logical request limit for one sync was reached."""


@dataclass
class RequestBudget:
    """Operator-configured bound on logical GETs; not a Zoom provider quota."""

    remaining: int = DEFAULT_REQUEST_LIMIT
    name: str = "request"
    lock: Lock = field(default_factory=Lock)

    def consume(self) -> None:
        with self.lock:
            if self.remaining <= 0:
                raise ZoomRequestLimitError(
                    f"Zoom sync reached its configured {self.name} limit"
                )
            self.remaining -= 1


class _CappedRetry(Retry):
    """Cap server-directed delays on the supported urllib3 2.0 dependency floor."""

    def get_retry_after(self, response: BaseHTTPResponse) -> float | None:
        retry_after = super().get_retry_after(response)
        if retry_after is None:
            return None
        return min(retry_after, 8)


class ZoomClient:
    """Account-scoped OAuth with three retries and capped Retry-After delays."""

    def __init__(
        self,
        account_id: str,
        client_id: str,
        client_secret: str,
        budget: RequestBudget | None = None,
    ) -> None:
        self.budget = budget if budget is not None else RequestBudget()
        self.account_id = account_id
        self.auth = (client_id, client_secret)
        self.session = requests.Session()
        self.session.mount(
            "https://",
            HTTPAdapter(
                max_retries=_CappedRetry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist={429, 500, 502, 503, 504},
                    # Token issuance can be retried; it does not invalidate existing tokens.
                    allowed_methods={"GET", "POST"},
                    raise_on_status=False,
                )
            ),
        )
        self._access_token = ""
        self._expires_at = 0.0

    def _refresh_token(self) -> None:
        response = self.session.post(
            TOKEN_URL,
            data={"grant_type": "account_credentials", "account_id": self.account_id},
            auth=self.auth,
            timeout=(10, 60),
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise requests.HTTPError(
                "Unexpected Zoom token response status", response=response
            )
        token = response.json()
        self._access_token = token["access_token"]
        self._expires_at = time.monotonic() + int(token["expires_in"]) - 60

    def fork(self) -> "ZoomClient":
        """Give an enrichment worker its own session and the shared request budget."""
        worker = ZoomClient(self.account_id, *self.auth, budget=self.budget)
        worker._access_token = self._access_token
        worker._expires_at = self._expires_at
        return worker

    def get_users_page(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.get("/users", params)

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        parsed = urlsplit(path)
        if (
            not path.startswith("/")
            or parsed.netloc
            or parsed.scheme
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Zoom API paths must be relative paths without query strings"
            )
        self.budget.consume()
        if time.monotonic() >= self._expires_at:
            self._refresh_token()
        # Refresh once on early revocation/expiry; a second 401 is fatal.
        for attempt in range(2):
            response = self.session.get(
                f"{API_URL}{path}",
                params=params,
                headers={"Authorization": f"Bearer {self._access_token}"},
                timeout=(10, 60),
                allow_redirects=False,
            )
            if response.status_code != 401 or attempt:
                break
            self._refresh_token()
        response.raise_for_status()
        if response.status_code != 200:
            raise requests.HTTPError(
                "Unexpected Zoom API response status", response=response
            )
        return response.json()

    def get_paginated(
        self,
        path: str,
        key: str,
        params: dict[str, Any] | None = None,
        page_size: int = 300,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        query = {"page_size": page_size, **(params or {})}
        seen_tokens: set[str] = set()
        for _ in range(DEFAULT_MAX_PAGES):
            page = self.get(path, query)
            records = page[key]
            if not isinstance(records, list):
                raise ValueError(f"Zoom {key} response must contain a list")
            result.extend(records)
            token = page.get("next_page_token")
            if not token:
                if len(result) < page.get("total_records", len(result)):
                    raise ValueError(
                        f"Zoom {key} pagination ended before all records were retrieved"
                    )
                return result
            if token in seen_tokens:
                raise ValueError(f"Zoom {key} returned a repeated pagination token")
            seen_tokens.add(token)
            query["next_page_token"] = token
        raise ValueError(f"Zoom {key} pagination exceeded the page limit")
