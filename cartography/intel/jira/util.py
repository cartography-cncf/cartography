from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import requests
from requests.adapters import HTTPAdapter

from cartography.client.http import CappedRetry
from cartography.util import DEFAULT_MAX_PAGES


class JiraClient:
    """Read-only Jira Cloud client with bounded retries and complete pagination."""

    def __init__(
        self, cloud_id: str, email: str, api_token: str, site_url: str | None = None
    ) -> None:
        # Cloud ID remains stable when a site is renamed and scopes every graph ID.
        self.cloud_id = str(UUID(cloud_id))
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
                max_retries=CappedRetry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=(429, 502, 503, 504),
                    allowed_methods=frozenset({"GET"}),
                    respect_retry_after_header=True,
                ),
            ),
        )

    def get(self, path: str, **params: Any) -> Any:
        response = self.session.get(
            f"{self.base_url}/rest/api/3/{path}",
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
            if path == "users/search":
                if not isinstance(page, list):
                    raise ValueError("Jira users response must be an array")
                values = page
                # This endpoint has no pagination metadata and may cap page size.
                done = not values
            else:
                values = page["values"]
                if page["startAt"] != start:
                    raise ValueError(
                        "Jira pagination did not advance to the requested offset"
                    )
                done = page.get("isLast")
                if done is None:
                    done = start + len(values) >= page["total"]
                if not isinstance(done, bool):
                    raise ValueError("Jira pagination isLast must be a boolean")
                if done and "total" in page and start + len(values) < page["total"]:
                    raise ValueError(
                        "Jira final page does not cover the reported total"
                    )
                if not values and not done:
                    raise ValueError("Jira returned an incomplete empty page")
            if not isinstance(values, list) or any(
                not isinstance(v, dict) for v in values
            ):
                raise ValueError("Jira page values must be objects")
            if values and values == previous:
                raise ValueError("Jira returned a repeated page")
            result.extend(values)
            if done:
                return result
            previous = values
            start += len(values)
        raise RuntimeError(
            f"Jira pagination exceeded {DEFAULT_MAX_PAGES} pages for {path}"
        )
