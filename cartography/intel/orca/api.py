import hashlib
import json
import logging
from collections.abc import Iterator
from typing import Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 120
REQUEST_TIMEOUT = (CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS)
SERVING_LAYER_PATH = "/api/serving-layer/query"
ORGANIZATION_PATH = "/api/user/action"
MAX_PAGES = 10_000
_PROGRESS_PAGE_INTERVAL = 10
_RETRY_STATUS_CODES = (408, 429, 502, 503, 504)


def normalize_api_endpoint(api_endpoint: str) -> str:
    """Validate and normalize a regional Orca API origin."""
    parsed = urlparse(api_endpoint.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Orca API endpoint must be an absolute HTTPS origin")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Orca API endpoint must not contain user information")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Orca API endpoint contains an invalid port") from exc
    if parsed.path.rstrip("/") or parsed.params or parsed.query or parsed.fragment:
        raise ValueError(
            "Orca API endpoint must be an origin without /api, a route, query, or fragment",
        )
    return f"https://{parsed.netloc}"


def create_session(api_token: str) -> requests.Session:
    """Create an Orca API session with bounded retries for read-only requests."""
    api_token = api_token.strip()
    if not api_token:
        raise ValueError("Orca API token must not be empty")

    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        other=0,
        allowed_methods=frozenset({"GET", "POST"}),
        status_forcelist=_RETRY_STATUS_CODES,
        backoff_factor=0.25,
        backoff_max=16,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Token {api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "cartography-orca",
        },
    )
    session.mount("https://", adapter)
    return session


def _request_json(
    session: requests.Session,
    method: str,
    api_endpoint: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    endpoint = normalize_api_endpoint(api_endpoint)
    try:
        response = session.request(
            method,
            f"{endpoint}{path}",
            json=json_body,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Orca {method} {path} request failed") from exc
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        status_code = response.status_code
        raise RuntimeError(
            f"Orca {method} {path} failed with HTTP {status_code}",
        ) from exc
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Orca {method} {path} returned invalid JSON",
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Orca {method} {path} returned a non-object response")
    return payload


def get_organization(
    session: requests.Session,
    api_endpoint: str,
) -> dict[str, str]:
    """Return the current Orca organization identity."""
    payload = _request_json(session, "GET", api_endpoint, ORGANIZATION_PATH)
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Orca organization response data must be an object")
    organization_id = data.get("organization_id")
    organization_name = data.get("organization_name")
    if not isinstance(organization_id, str) or not organization_id.strip():
        raise RuntimeError("Orca organization response omitted organization_id")
    if not isinstance(organization_name, str) or not organization_name.strip():
        raise RuntimeError("Orca organization response omitted organization_name")
    return {
        "id": organization_id.strip(),
        "name": organization_name.strip(),
        "api_url": normalize_api_endpoint(api_endpoint),
    }


def serving_layer_query(
    session: requests.Session,
    api_endpoint: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Execute one read-only Orca Serving Layer query."""
    return _request_json(
        session,
        "POST",
        api_endpoint,
        SERVING_LAYER_PATH,
        json_body=payload,
    )


def _require_total_items(value: Any, error_message: str) -> int:
    # bool subclasses int, but is not a valid API item count.
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError(error_message)
    return value


def iter_serving_layer_pages(
    session: requests.Session,
    api_endpoint: str,
    query: dict[str, Any],
    *,
    page_size: int,
    result_name: str,
    max_pages: int = MAX_PAGES,
) -> Iterator[list[dict[str, Any]]]:
    """Yield complete Orca result pages while enforcing pagination invariants."""
    if page_size < 1:
        raise ValueError("Orca page size must be greater than zero")
    if max_pages < 1:
        raise ValueError("Orca max_pages must be greater than zero")

    start_index = 0
    total_items: int | None = None
    page_count = 0
    page_signatures: set[str] = set()

    while True:
        if page_count >= max_pages:
            raise RuntimeError(
                f"Orca {result_name} pagination exceeded {max_pages} pages",
            )

        payload = {
            **query,
            "limit": page_size,
            "start_at_index": start_index,
            "get_results_and_count": total_items is None,
        }
        response = serving_layer_query(session, api_endpoint, payload)

        rows = response.get("data")
        if not isinstance(rows, list):
            raise RuntimeError(f"Orca {result_name} response omitted data list")
        if any(not isinstance(row, dict) for row in rows):
            raise RuntimeError(
                f"Orca {result_name} response contained a non-object row"
            )

        response_total = response.get("total_items")
        if total_items is None:
            total_items = _require_total_items(
                response_total,
                f"Orca {result_name} response omitted integer total_items",
            )
            if total_items < 0:
                raise RuntimeError(
                    f"Orca {result_name} response returned negative total_items",
                )
            required_pages = (total_items + page_size - 1) // page_size
            if required_pages > max_pages:
                raise RuntimeError(
                    f"Orca {result_name} requires {required_pages} pages, "
                    f"exceeding the {max_pages}-page safety limit",
                )
        elif response_total is not None:
            response_total = _require_total_items(
                response_total,
                f"Orca {result_name} returned a malformed total_items",
            )
            if response_total != total_items:
                raise RuntimeError(
                    f"Orca {result_name} total_items changed during pagination",
                )

        if len(rows) > page_size:
            raise RuntimeError(
                f"Orca {result_name} returned more rows than the requested page size",
            )

        if not rows:
            if start_index != total_items:
                raise RuntimeError(
                    f"Orca {result_name} pagination stopped at {start_index} "
                    f"of {total_items} rows",
                )
            return

        page_signature = hashlib.sha256(
            json.dumps(rows, sort_keys=True, separators=(",", ":")).encode(),
        ).hexdigest()
        if page_signature in page_signatures:
            raise RuntimeError(f"Orca {result_name} pagination repeated a page")
        page_signatures.add(page_signature)

        next_index = start_index + len(rows)
        if next_index > total_items:
            raise RuntimeError(
                f"Orca {result_name} returned more rows than total_items",
            )

        page_count += 1
        yield rows
        start_index = next_index

        if page_count % _PROGRESS_PAGE_INTERVAL == 0:
            logger.debug(
                "Fetched %d of %d Orca %s across %d pages.",
                start_index,
                total_items,
                result_name,
                page_count,
            )
        if start_index == total_items:
            return
