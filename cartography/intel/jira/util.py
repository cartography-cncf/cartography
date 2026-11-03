from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import requests
from requests.adapters import HTTPAdapter
from urllib3.response import BaseHTTPResponse
from urllib3.util.retry import Retry

from cartography.util import DEFAULT_MAX_PAGES


def require_array(value: Any, context: str) -> list[Any]:
    # An empty object must not masquerade as an empty inventory.
    if not isinstance(value, list):
        raise ValueError(f"Jira {context} must be an array")
    return value


class _CappedRetry(Retry):
    def get_retry_after(self, response: BaseHTTPResponse) -> float | None:
        retry_after = super().get_retry_after(response)
        return min(retry_after, 8) if retry_after is not None else None


class JiraClient:
    """Read-only Jira Cloud client with bounded retries and complete pagination."""

    def __init__(
        self, cloud_id: str, email: str, api_token: str, site_url: str | None = None
    ) -> None:
        # Cloud ID remains stable when a site is renamed and scopes every graph ID.
        self.cloud_id = str(UUID(cloud_id))
        self.site_url = site_url
        self.base_url = f"https://api.atlassian.com/ex/jira/{self.cloud_id}"
        if site_url:
            parsed = urlsplit(site_url)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or not parsed.hostname.endswith(".atlassian.net")
                or parsed.username
                or parsed.password
                or parsed.port not in (None, 443)
                or parsed.path not in ("", "/")
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(
                    "jira-site-url must be an HTTPS *.atlassian.net origin"
                )
            self.base_url = site_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({"Accept": "application/json"})
        self.session.mount(
            "https://",
            HTTPAdapter(
                max_retries=_CappedRetry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=(429, 502, 503, 504),
                    allowed_methods=frozenset({"GET"}),
                    respect_retry_after_header=True,
                ),
            ),
        )

    def get(self, path: str, **params: Any) -> Any:
        return self._get_json(f"{self.base_url}/rest/api/3/{path}", **params)

    def validate_site(self) -> None:
        """Reject a site override that would write into another tenant's scope."""
        if self.site_url is not None:
            info = self._get_json(f"{self.base_url}/_edge/tenant_info")
            if str(UUID(info["cloudId"])) != self.cloud_id:
                raise ValueError("jira-site-url does not match jira-cloud-id")

    def _get_json(self, url: str, **params: Any) -> Any:
        response = self.session.get(
            url,
            params=params,
            timeout=(10, 60),
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.is_redirect:
            raise requests.HTTPError(
                "Jira API unexpectedly redirected", response=response
            )
        return response.json()

    def pages(self, path: str, **params: Any) -> list[dict[str, Any]]:
        """Read PageBeans, or the unwrapped /users/search array, to completion."""
        result: list[dict[str, Any]] = []
        start = 0
        previous = None
        for _ in range(DEFAULT_MAX_PAGES):
            page = self.get(
                path,
                startAt=start,
                maxResults=1000 if path == "users/search" else 50,
                **params,
            )
            context = f"{path} at startAt={start}"
            values = require_array(
                page if path == "users/search" else page["values"], context
            )
            if path == "users/search":
                # This endpoint has no pagination metadata and may cap page size.
                done = not values
            else:
                if page["startAt"] != start:
                    raise ValueError(
                        f"Jira {context}: pagination did not advance to the requested offset"
                    )
                done = page.get("isLast")
                if done is None:
                    done = start + len(values) >= page["total"]
                if not isinstance(done, bool):
                    raise ValueError(f"Jira {context}: isLast must be a boolean")
                if done and "total" in page and start + len(values) < page["total"]:
                    raise ValueError(
                        f"Jira {context}: final page does not cover the reported total"
                    )
                if not values and not done:
                    raise ValueError(f"Jira {context}: incomplete empty page")
            if values and values == previous:
                raise ValueError(f"Jira {context}: repeated page")
            result.extend(values)
            if done:
                return result
            previous = values
            start += len(values)
        raise RuntimeError(
            f"Jira pagination exceeded {DEFAULT_MAX_PAGES} pages for {path}"
        )
