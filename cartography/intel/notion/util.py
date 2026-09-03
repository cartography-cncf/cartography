import base64
import binascii
import json
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


def parse_config(encoded_config: str) -> list[NotionWorkspaceConfig]:
    try:
        decoded = base64.b64decode(encoded_config, validate=True).decode("utf-8")
        config = json.loads(decoded)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Notion config must be valid base64-encoded JSON") from error

    if not isinstance(config, dict):
        raise ValueError("Notion config must be a JSON object")
    workspaces = config.get("workspaces")
    if not isinstance(workspaces, list) or not workspaces:
        raise ValueError("Notion config must contain a non-empty workspaces list")

    parsed: list[NotionWorkspaceConfig] = []
    seen_tokens: set[str] = set()
    for workspace in workspaces:
        if not isinstance(workspace, dict):
            raise ValueError("Each Notion workspace config must be a JSON object")
        api_token = workspace.get("api_token")
        if not isinstance(api_token, str) or not api_token.strip():
            raise ValueError(
                "Notion workspace config field 'api_token' must be a non-empty string"
            )
        api_token = api_token.strip()
        if api_token in seen_tokens:
            raise ValueError("Notion config contains a duplicate API token")
        seen_tokens.add(api_token)

        sync_public_pages = workspace.get("sync_public_pages", False)
        if not isinstance(sync_public_pages, bool):
            raise ValueError(
                "Notion workspace config field 'sync_public_pages' must be a boolean"
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
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Notion paginated response must be a JSON object")

        page_results = payload.get("results")
        has_more = payload.get("has_more")
        if not isinstance(page_results, list) or not all(
            isinstance(item, dict) for item in page_results
        ):
            raise ValueError("Notion paginated response must contain object results")
        if not isinstance(has_more, bool):
            raise ValueError("Notion paginated response must contain boolean has_more")
        results.extend(page_results)

        if not has_more:
            return results

        next_cursor_value = payload.get("next_cursor")
        if not isinstance(next_cursor_value, str) or not next_cursor_value:
            raise ValueError("Notion paginated response is missing next_cursor")
        if next_cursor_value in seen_cursors:
            raise ValueError("Notion pagination returned a repeated cursor")
        seen_cursors.add(next_cursor_value)
        next_cursor = next_cursor_value


def scoped_id(workspace_id: str, notion_id: str) -> str:
    return f"{workspace_id}/{notion_id}"


def post_paginated(
    api_session: requests.Session,
    endpoint: str,
    body: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
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
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Notion paginated response must be a JSON object")

        page_results = payload.get("results")
        has_more = payload.get("has_more")
        if not isinstance(page_results, list) or not all(
            isinstance(item, dict) for item in page_results
        ):
            raise ValueError("Notion paginated response must contain object results")
        if not isinstance(has_more, bool):
            raise ValueError("Notion paginated response must contain boolean has_more")
        results.extend(page_results)

        if not has_more:
            return results

        next_cursor_value = payload.get("next_cursor")
        if not isinstance(next_cursor_value, str) or not next_cursor_value:
            raise ValueError("Notion paginated response is missing next_cursor")
        if next_cursor_value in seen_cursors:
            raise ValueError("Notion pagination returned a repeated cursor")
        seen_cursors.add(next_cursor_value)
        next_cursor = next_cursor_value
