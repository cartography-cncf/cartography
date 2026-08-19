import logging
from typing import Any
from typing import Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)

BASE_URL = "https://api.runpod.io/v2"
SKIPPED_SYNC = object()


def build_session(api_key: str) -> requests.Session:
    session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    return session


def require_non_empty(value: Any, field_name: str) -> Any:
    if value is None or value == "":
        raise ValueError(f"RunPod record is missing required non-empty {field_name}.")
    return value


def first_present(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return None


def first_not_none(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value is not None:
            return value
    return None


def first_present_list(record: dict[str, Any], *keys: str) -> list[Any]:
    for key in keys:
        if key in record:
            value = record[key]
            if value is None:
                return []
            if not isinstance(value, list):
                raise ValueError(
                    f"RunPod field {key!r} must be a list, got {type(value).__name__}."
                )
            return value
    return []


def id_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(
            f"RunPod field {field_name!r} must be a list, got {type(value).__name__}."
        )

    ids = []
    for entry in value:
        if entry is None:
            continue
        if isinstance(entry, dict):
            ids.append(
                str(require_non_empty(entry.get("id"), f"{field_name} entry id"))
            )
        else:
            ids.append(str(entry))
    return ids


def _unwrap_list_response(
    body: Any,
    path: str,
    list_keys: tuple[str, ...],
) -> list[Any]:
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        for key in list_keys:
            value = body.get(key)
            if isinstance(value, list):
                return value
        raise ValueError(
            f"RunPod API returned an object response for {path} without one of "
            f"the expected list keys {sorted(list_keys)!r}; got keys "
            f"{sorted(body.keys())!r}."
        )
    raise ValueError(
        f"RunPod API returned a non-list response for {path}: {type(body).__name__}."
    )


def get_list(
    session: requests.Session,
    base_url: str,
    path: str,
    list_keys: tuple[str, ...],
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch a RunPod v2 list endpoint.

    RunPod's documented v2 list endpoints used by this module return a single object
    wrapper such as {"pods": [...]} or {"networkVolumes": [...]}, with no documented
    cursor, next-page token, or total count. Keep this as one GET until the API docs
    expose a supported pagination contract; guessing from response keys like "cursor"
    or "next" would risk skipped or duplicated inventory before scoped cleanup.
    """
    response = session.get(f"{base_url}{path}", params=params, timeout=(60, 60))
    response.raise_for_status()
    try:
        body = response.json()
    except ValueError as exc:
        raise ValueError(f"RunPod API returned malformed JSON for {path}.") from exc

    records = _unwrap_list_response(body, path, list_keys)

    for record in records:
        if not isinstance(record, dict):
            raise ValueError(
                f"RunPod API returned a malformed entry for {path}: expected an "
                f"object, got {type(record).__name__}."
            )
    return records


def get_string_list(
    session: requests.Session,
    base_url: str,
    path: str,
    list_keys: tuple[str, ...],
) -> list[str]:
    response = session.get(f"{base_url}{path}", timeout=(60, 60))
    response.raise_for_status()
    try:
        body = response.json()
    except ValueError as exc:
        raise ValueError(f"RunPod API returned malformed JSON for {path}.") from exc

    records = _unwrap_list_response(body, path, list_keys)

    for record in records:
        if not isinstance(record, str):
            raise ValueError(
                f"RunPod API returned a malformed entry for {path}: expected a "
                f"string, got {type(record).__name__}."
            )
    return records


def _compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in value.items() if v is not None}


def compact_json(value: Any) -> Any:
    if isinstance(value, dict):
        return _compact_dict({k: compact_json(v) for k, v in value.items()})
    if isinstance(value, list):
        return [compact_json(v) for v in value]
    return value


def safe_sync(
    name: str,
    sync_fn: Callable[..., Any],
    required: bool,
    **kwargs: Any,
) -> Any:
    try:
        return sync_fn(**kwargs)
    except requests.exceptions.RequestException as exc:
        if required:
            raise
        logger.warning(
            "RunPod %s sync failed - skipping this resource type and its cleanup "
            "for this run, continuing with the rest of the account sync: %s",
            name,
            exc,
        )
        return SKIPPED_SYNC
