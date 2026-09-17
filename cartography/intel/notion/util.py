import base64
import binascii
import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

NOTION_API_BASE_URL = "https://api.notion.com/v1"
NOTION_API_VERSION = "2026-03-11"
REQUEST_TIMEOUT = (60, 60)


@dataclass(frozen=True)
class NotionWorkspaceConfig:
    api_token: str
    sync_public_pages: bool


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string or null")
    return value


def require_boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def parse_config(encoded_config: str) -> list[NotionWorkspaceConfig]:
    try:
        decoded = base64.b64decode(encoded_config, validate=True).decode("utf-8")
        config = json.loads(decoded)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Notion config must be valid base64-encoded JSON") from error

    config = require_object(config, "Notion config")
    workspaces = config.get("workspaces")
    if not isinstance(workspaces, list) or not workspaces:
        raise ValueError("Notion config must contain a non-empty workspaces list")

    parsed: list[NotionWorkspaceConfig] = []
    seen_tokens: set[str] = set()
    for workspace in workspaces:
        workspace = require_object(workspace, "Notion workspace config")
        api_token = require_nonempty_string(
            workspace.get("api_token"),
            "Notion workspace config field 'api_token'",
        )
        api_token = api_token.strip()
        if api_token in seen_tokens:
            raise ValueError("Notion config contains a duplicate API token")
        seen_tokens.add(api_token)

        sync_public_pages = workspace.get("sync_public_pages", False)
        sync_public_pages = require_boolean(
            sync_public_pages,
            "Notion workspace config field 'sync_public_pages'",
        )
        parsed.append(NotionWorkspaceConfig(api_token, sync_public_pages))

    return parsed


def create_api_session(api_token: str) -> requests.Session:
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        # Notion's search endpoint is a read-only POST operation.
        allowed_methods=frozenset({"GET", "POST"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.headers.update(
        {
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": NOTION_API_VERSION,
            "Accept": "application/json",
        },
    )
    return session


def get_paginated(
    api_session: requests.Session,
    endpoint: str,
    expected_type: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    next_cursor: str | None = None
    seen_cursors: set[str] = set()

    while True:
        params: dict[str, Any] = {"page_size": 100}
        if next_cursor is not None:
            params["start_cursor"] = next_cursor
        response = api_session.get(
            f"{NOTION_API_BASE_URL}/{endpoint}",
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        page_results, has_more, next_cursor_value = _validate_paginated_payload(
            response.json(),
            expected_type,
        )
        results.extend(page_results)

        if not has_more:
            return results

        next_cursor_value = require_nonempty_string(
            next_cursor_value,
            "Notion paginated response next_cursor",
        )
        if next_cursor_value in seen_cursors:
            raise ValueError("Notion pagination returned a repeated cursor")
        seen_cursors.add(next_cursor_value)
        next_cursor = next_cursor_value


def scoped_id(workspace_id: str, notion_id: str) -> str:
    return f"{workspace_id}/{notion_id}"


def _validate_paginated_payload(
    payload: Any,
    expected_type: str,
) -> tuple[list[dict[str, Any]], bool, Any]:
    payload = require_object(payload, "Notion paginated response")
    if payload.get("object") != "list" or payload.get("type") != expected_type:
        raise ValueError("Notion paginated response has an unexpected object type")
    require_object(
        payload.get(expected_type),
        "Notion paginated response type metadata",
    )

    page_results = payload.get("results")
    has_more = payload.get("has_more")
    if not isinstance(page_results, list) or not all(
        isinstance(item, dict) for item in page_results
    ):
        raise ValueError("Notion paginated response must contain object results")
    has_more = require_boolean(has_more, "Notion paginated response has_more")
    return page_results, has_more, payload.get("next_cursor")


def post_paginated(
    api_session: requests.Session,
    endpoint: str,
    body: dict[str, Any],
    expected_type: str,
) -> Iterator[list[dict[str, Any]]]:
    next_cursor: str | None = None
    seen_cursors: set[str] = set()

    while True:
        request_body = {**body, "page_size": 100}
        if next_cursor is not None:
            request_body["start_cursor"] = next_cursor
        response = api_session.post(
            f"{NOTION_API_BASE_URL}/{endpoint}",
            json=request_body,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        page_results, has_more, next_cursor_value = _validate_paginated_payload(
            response.json(),
            expected_type,
        )
        yield page_results

        if not has_more:
            return

        next_cursor_value = require_nonempty_string(
            next_cursor_value,
            "Notion paginated response next_cursor",
        )
        if next_cursor_value in seen_cursors:
            raise ValueError("Notion pagination returned a repeated cursor")
        seen_cursors.add(next_cursor_value)
        next_cursor = next_cursor_value
