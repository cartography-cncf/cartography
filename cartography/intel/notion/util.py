import base64
import binascii
import json
from dataclasses import dataclass
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

NOTION_API_BASE_URL = "https://api.notion.com/v1"
NOTION_SCIM_BASE_URL = "https://api.notion.com/scim/v2"
NOTION_API_VERSION = "2026-03-11"
REQUEST_TIMEOUT = (60, 60)


@dataclass(frozen=True)
class NotionWorkspaceConfig:
    workspace_id: str
    workspace_name: str
    api_token: str
    scim_token: str | None = None


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
    seen_ids: set[str] = set()
    for workspace in workspaces:
        if not isinstance(workspace, dict):
            raise ValueError("Each Notion workspace config must be a JSON object")
        values: dict[str, Any] = {}
        for field in ("workspace_id", "workspace_name", "api_token"):
            value = workspace.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Notion workspace config field {field!r} must be a non-empty string"
                )
            values[field] = value.strip()

        scim_token = workspace.get("scim_token")
        if scim_token is not None and (
            not isinstance(scim_token, str) or not scim_token.strip()
        ):
            raise ValueError(
                "Notion workspace config field 'scim_token' must be a non-empty string"
            )
        values["scim_token"] = scim_token.strip() if scim_token else None

        if values["workspace_id"] in seen_ids:
            raise ValueError(
                f"Duplicate Notion workspace ID {values['workspace_id']!r}"
            )
        seen_ids.add(values["workspace_id"])
        parsed.append(NotionWorkspaceConfig(**values))

    return parsed


def create_api_session(api_token: str) -> requests.Session:
    return _create_session(
        api_token,
        {
            "Notion-Version": NOTION_API_VERSION,
            "Accept": "application/json",
        },
    )


def create_scim_session(scim_token: str) -> requests.Session:
    return _create_session(scim_token, {"Accept": "application/scim+json"})


def _create_session(api_token: str, headers: dict[str, str]) -> requests.Session:
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.headers.update({"Authorization": f"Bearer {api_token}", **headers})
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


def get_scim_paginated(
    scim_session: requests.Session,
    resource: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    start_index = 1
    expected_total: int | None = None

    while True:
        response = scim_session.get(
            f"{NOTION_SCIM_BASE_URL}/{resource}",
            params={"startIndex": start_index, "count": 100},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Notion SCIM response must be a JSON object")

        resources = payload.get("Resources")
        total = payload.get("totalResults")
        response_start = payload.get("startIndex")
        page_size = payload.get("itemsPerPage")
        if not isinstance(resources, list) or not all(
            isinstance(item, dict) for item in resources
        ):
            raise ValueError("Notion SCIM response must contain object Resources")
        if not isinstance(total, int) or isinstance(total, bool) or total < 0:
            raise ValueError("Notion SCIM response has an invalid totalResults")
        if (
            not isinstance(response_start, int)
            or isinstance(response_start, bool)
            or response_start != start_index
        ):
            raise ValueError("Notion SCIM response has an unexpected startIndex")
        if (
            not isinstance(page_size, int)
            or isinstance(page_size, bool)
            or page_size != len(resources)
        ):
            raise ValueError("Notion SCIM response has an invalid itemsPerPage")
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise ValueError("Notion SCIM totalResults changed during pagination")

        results.extend(resources)
        if len(results) == expected_total:
            return results
        if not resources or len(results) > expected_total:
            raise ValueError("Notion SCIM pagination did not make valid progress")
        start_index += len(resources)
