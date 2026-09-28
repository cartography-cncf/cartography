import logging
from datetime import datetime
from typing import Any

import requests
import xmltodict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)
_DEFAULT_PAGE_SIZE = 500
# Miradore formats dates with a .NET format string. Pin it to an unambiguous, sortable
# layout instead of the default `dd.MM.yyyy HH:mm:ss`. A literal `T` would need escaping
# in a .NET format string, so use a space separator.
_API_DATE_FORMAT = "yyyy-MM-dd HH:mm:ss"
_PYTHON_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_TRUE_VALUES = {"true", "1", "yes"}
_FALSE_VALUES = {"false", "0", "no"}


@timeit
def create_miradore_api_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/xml"})
    # A single transient blip on any page would otherwise abort the whole Miradore sync.
    # Every call this module makes is an idempotent GET, so bounded retries are safe.
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    return session


def _build_item_uri(base_uri: str, site_name: str, item: str) -> str:
    return f"{base_uri.rstrip('/')}/{site_name}/API/{item}"


def _build_options(page: int, page_size: int) -> str:
    return f"rows={page_size},page={page},dateformat={_API_DATE_FORMAT}"


def _extract_items(payload: dict[str, Any], item: str) -> list[dict[str, Any]]:
    """Pull the `<Item>` elements out of a parsed `<Content><Items>` document.

    xmltodict collapses a single repeated element into a dict rather than a one-element
    list, and omits the key entirely when the page is empty, so normalize both here.

    A document that is not the documented envelope must not be mistaken for an empty
    page: an error or sign-in page served with HTTP 200 would otherwise yield no rows,
    and the cleanup that follows would delete the resource's existing nodes. Raise
    instead, while still accepting a genuine `<Items count="0" />`.
    """
    content = payload.get("Content")
    if not isinstance(content, dict) or "Items" not in content:
        raise ValueError(
            "Miradore API returned a document without the expected <Content><Items> "
            f"envelope while fetching {item}; refusing to treat it as an empty result",
        )
    items = content["Items"]
    # `<Items />` parses to None and `<Items count="0" />` to just its attributes.
    # Both are legitimately empty pages.
    if not isinstance(items, dict):
        return []
    entries = items.get(item)
    if entries is None:
        return []
    if isinstance(entries, list):
        return entries
    return [entries]


def _get_page_without_disclosing_the_api_key(
    api_session: requests.Session,
    uri: str,
    params: dict[str, str],
    page: int,
) -> requests.Response:
    """Fetch one page, turning any failure into an error that omits the API key.

    API v1 authenticates through an `auth` query parameter, so the prepared URL embeds the
    key. Every way this request can fail puts that URL in the exception message, and the
    sync runner logs the exception:

    - a transport failure, including a connection error, a timeout, and an exhausted retry
      (`RetryError`), which `requests` raises out of `Session.get` itself;
    - an error status, which `Response.raise_for_status()` would report with the full URL.

    So re-raise with the key-free request path in both cases. `from None` suppresses the
    exception chain, otherwise the original message would resurface in the traceback, and
    no response is attached so no caller can read `response.url` either.
    """
    try:
        response = api_session.get(uri, params=params, timeout=_TIMEOUT)
    except requests.exceptions.RequestException as err:
        # The exception type is the diagnosable part; its message is not safe to keep.
        raise requests.exceptions.RequestException(
            f"Miradore API request to {uri} (page {page}) failed with "
            f"{type(err).__name__}",
        ) from None
    if not response.ok:
        raise requests.HTTPError(
            f"Miradore API returned HTTP {response.status_code} for {uri} (page {page})",
        )
    return response


@timeit
def get_paginated_miradore_items(
    api_session: requests.Session,
    base_uri: str,
    site_name: str,
    api_key: str,
    item: str,
    select: str,
    page_size: int = _DEFAULT_PAGE_SIZE,
) -> list[dict[str, Any]]:
    """Fetch every page of a Miradore API v1 `get` operation for the given item type."""
    uri = _build_item_uri(base_uri, site_name, item)
    page = 1
    results: list[dict[str, Any]] = []

    while True:
        # The API key travels in the query string, so it must only ever be passed via
        # `params`. Never interpolate it into a URI that could reach a log line.
        params = {
            "auth": api_key,
            "select": select,
            "options": _build_options(page, page_size),
        }
        response = _get_page_without_disclosing_the_api_key(
            api_session,
            uri,
            params,
            page,
        )

        page_results = _extract_items(xmltodict.parse(response.text), item)
        results.extend(page_results)
        if len(page_results) < page_size:
            return results
        page += 1


def required_int_id(item: dict[str, Any], item_type: str) -> int:
    """Return the required `ID` of a Miradore item, failing loudly when it is unusable.

    The ID becomes the graph identity, so a null one would reach the ingestion `MERGE` as
    `id: None` and corrupt the graph. Reject the record at the API boundary instead.
    Indexing directly raises `KeyError` when the attribute is absent, and the explicit
    check covers an `ID` that is present but not the documented Int32.
    """
    raw_id = item["ID"]
    parsed = parse_int(raw_id)
    if parsed is None:
        raise ValueError(
            f"Miradore returned a {item_type} whose ID is not an integer: {raw_id!r}"
        )
    return parsed


def scoped_id(site_name: str, native_id: Any) -> str | None:
    """Build a graph identity that is unique across Miradore tenants.

    Miradore numbers items per tenant, so `Device` 1001 exists in every site. The graph
    merges nodes on `id` alone, so the raw API identifier would make two sites overwrite
    each other's devices and cross-wire their relationships. Prefix it with the site name,
    which cannot itself contain a `/`, so the composition stays unambiguous.
    """
    if native_id is None:
        return None
    return f"{site_name}/{native_id}"


def get_nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def as_list(value: Any) -> list[Any]:
    """Normalize a Miradore `List` typed attribute into a list.

    xmltodict returns a dict for a single child element and omits the key when the list
    is empty, so callers cannot assume a list.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def parse_datetime(value: Any) -> datetime | None:
    """Parse a Miradore date-time rendered with `_API_DATE_FORMAT`."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), _PYTHON_DATE_FORMAT)
    except ValueError:
        logger.warning("Miradore: could not parse '%s' as a date-time.", value)
        return None


def parse_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return int(value.strip())
    except ValueError:
        logger.warning("Miradore: could not parse '%s' as an integer.", value)
        return None


def parse_bool(value: Any) -> bool | None:
    """Parse a Miradore `Boolean` attribute, which xmltodict surfaces as a string."""
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return None
