import logging
import random
import time
from typing import Any
from urllib.parse import urljoin

import requests
import yaml

logger = logging.getLogger(__name__)

RETRYABLE_STATUSES = {408, 429, 504}


class SysdigClient:
    def __init__(
        self,
        api_url: str,
        api_token: str,
        page_size: int = 1000,
        timeout: int = 60,
        max_attempts: int = 4,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token
        self.page_size = page_size
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.session = requests.Session()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        url = urljoin(f"{self.api_url}/", path.lstrip("/"))
        for attempt in range(self.max_attempts):
            try:
                response = self.session.request(
                    method,
                    url,
                    headers=self._headers(),
                    timeout=self.timeout,
                    **kwargs,
                )
            except (requests.ConnectionError, requests.Timeout):
                if attempt == self.max_attempts - 1:
                    raise
                self._sleep(attempt)
                continue

            if response.status_code in RETRYABLE_STATUSES:
                if attempt == self.max_attempts - 1:
                    response.raise_for_status()
                self._sleep(attempt)
                continue

            response.raise_for_status()
            return response

        raise RuntimeError("Sysdig request retry loop exited unexpectedly")

    @staticmethod
    def _sleep(attempt: int) -> None:
        time.sleep(min(2**attempt, 30) + random.uniform(0, 1))

    def get_schema(self) -> dict[str, Any]:
        response = self._request("GET", "/api/sysql/v2/schema")
        try:
            data = response.json()
        except ValueError:
            data = yaml.safe_load(response.text)
        if isinstance(data, dict):
            return data
        return {"schema": data}

    def query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        page_size: int | None = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        limit = page_size or self.page_size
        offset = 0

        while True:
            paged_query = f"{query.rstrip().rstrip(';')} LIMIT {limit} OFFSET {offset}"
            payload: dict[str, Any] = {"query": paged_query}
            if parameters:
                payload["parameters"] = parameters

            response = self._request(
                "POST",
                "/api/sysql/v2/query",
                json=payload,
            )
            page = _extract_rows(response.json())
            rows.extend(page)

            if len(page) < limit:
                break
            offset += limit

        return rows


def _extract_rows(response_json: Any) -> list[dict[str, Any]]:
    if isinstance(response_json, list):
        return [row for row in response_json if isinstance(row, dict)]
    if not isinstance(response_json, dict):
        return []

    for key in ("data", "results", "items", "rows"):
        value = response_json.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]

    return []


def schema_has_entity(schema: dict[str, Any], entity_name: str) -> bool:
    needle = entity_name.lower()

    def _walk(value: Any) -> bool:
        if isinstance(value, str):
            return value.lower() == needle
        if isinstance(value, dict):
            if any(isinstance(key, str) and key.lower() == needle for key in value):
                return True
            name = value.get("name") or value.get("label") or value.get("entity")
            if isinstance(name, str) and name.lower() == needle:
                return True
            return any(_walk(v) for v in value.values())
        if isinstance(value, list):
            return any(_walk(item) for item in value)
        return False

    return _walk(schema)
