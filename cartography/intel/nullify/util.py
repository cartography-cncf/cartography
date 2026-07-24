import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# (connect timeout, read timeout) in seconds.
_TIMEOUT = (60, 60)
_DEFAULT_PAGE_SIZE = 100


def build_base_url(tenant: str, base_url_override: str | None = None) -> str:
    """
    Build the Nullify API base URL. Nullify is tenant-scoped: each tenant is served
    from ``https://api.<tenant>.nullify.ai``. ``base_url_override`` lets operators point
    at a non-standard host (self-hosted / testing). No trailing slash.
    """
    if base_url_override:
        return base_url_override.rstrip("/")
    return f"https://api.{tenant}.nullify.ai"


class NullifyEnvelopeError(RuntimeError):
    """
    Raised when a Nullify response does not contain the expected item-collection key.

    This must NOT be swallowed into an empty list: a caller that treats "no items" as a
    legitimately-empty collection would run its cleanup and delete every previously
    ingested node. Raising instead lets the per-resource isolation skip load + cleanup,
    preserving prior data, and surfaces the envelope change.
    """


def _extract_items(payload: dict[str, Any], data_key: str) -> list[dict[str, Any]]:
    """
    Pull the item collection out of a Nullify response envelope.

    Robust to two shapes the API has been observed to use:
      - the collection value is a JSON array (the common case), or
      - the collection value is an indexed object (id -> item map), in which case we
        return its values.
    The envelope key is matched case-insensitively (some endpoints capitalise it, e.g.
    ``Users`` vs ``users``). A key that is present but ``null`` is a legitimately-empty
    collection and yields ``[]``; a key that is entirely absent is treated as a malformed
    or changed envelope and raises ``NullifyEnvelopeError`` (never a silent empty list,
    which would let cleanup delete previously-ingested nodes).
    """
    if data_key in payload:
        value = payload[data_key]
    else:
        lowered = {k.lower(): k for k in payload}
        actual_key = lowered.get(data_key.lower())
        if actual_key is None:
            raise NullifyEnvelopeError(
                f"Nullify response is missing the expected '{data_key}' collection; "
                f"got keys {sorted(payload)}",
            )
        value = payload[actual_key]

    if value is None:
        return []
    if isinstance(value, dict):
        return list(value.values())
    return list(value)


def paginate(
    api_session: requests.Session,
    url: str,
    data_key: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    GET every page of a Nullify list endpoint and return the concatenated items.

    Nullify uses cursor-based pagination: the response carries the item collection under
    ``data_key`` plus a ``nextToken`` cursor. When ``nextToken`` is empty or absent we
    have reached the last page. Endpoints that are not paginated (e.g. ``/admin/users``)
    simply omit ``nextToken``, so this makes a single request for them.

    Raises for HTTP errors (no exception swallowing) so the caller can decide whether to
    skip the resource.
    """
    results: list[dict[str, Any]] = []
    request_params = {"limit": _DEFAULT_PAGE_SIZE, **(params or {})}
    next_token: str | None = None

    while True:
        if next_token:
            request_params["nextToken"] = next_token
        response = api_session.get(url, params=request_params, timeout=_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        results.extend(_extract_items(payload, data_key))

        next_token = payload.get("nextToken")
        if not next_token:
            break

    return results
