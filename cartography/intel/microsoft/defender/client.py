import logging
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

import requests
from azure.core.credentials import TokenCredential
from azure.core.exceptions import ClientAuthenticationError
from dateutil.parser import isoparse
from requests.adapters import HTTPAdapter

from cartography.client.http import CappedRetry
from cartography.util import DEFAULT_MAX_PAGES

logger = logging.getLogger(__name__)
# Token error when the tenant has no Defender for Endpoint service principal.
RESOURCE_NOT_PROVISIONED = "AADSTS500011"


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=CappedRetry(
                total=5,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
            ),
        ),
    )
    return session


def get_collection(
    session: requests.Session,
    credential: TokenCredential,
    url: str,
    scope: str,
    params: dict[str, Any],
    *,
    use_skip: bool = False,
) -> list[dict[str, Any]]:
    """Read a complete collection; malformed or incomplete responses are fatal."""
    endpoint = urlsplit(url)
    query: dict[str, Any] | None = dict(params)
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_links: set[str] = set()
    for _ in range(DEFAULT_MAX_PAGES):
        # Azure Identity caches tokens and refreshes them when necessary.
        token = credential.get_token(scope).token
        response = session.get(
            url,
            params=query,
            headers={"Authorization": f"Bearer {token}"},
            timeout=(10, 60),
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError("Defender API returned an unexpected HTTP status")
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("value"), list):
            raise ValueError("Defender API response is missing its value collection")
        items = payload["value"]
        for item in items:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("id"), str)
                or not item["id"]
            ):
                raise ValueError("Defender API returned a record without an ID")
            if item["id"] in seen_ids:
                raise ValueError("Defender API pagination repeated a record")
            seen_ids.add(item["id"])
        results.extend(items)
        next_link = payload.get("@odata.nextLink")
        if next_link is not None:
            if not isinstance(next_link, str) or not next_link:
                raise ValueError("Defender API returned an invalid nextLink")
            next_url = urlsplit(next_link)
            if (
                next_url.scheme != endpoint.scheme
                or next_url.netloc != endpoint.netloc
                or next_url.path != endpoint.path
                or next_url.fragment
                or next_link in seen_links
            ):
                raise ValueError("Defender API returned an unsafe or repeated nextLink")
            seen_links.add(next_link)
            url, query = next_link, None
        elif use_skip and len(items) == params["$top"]:
            # MDE documents $top/$skip; a full page without nextLink is not EOF.
            url = endpoint.geturl()
            query = {**params, "$skip": len(results)}
        else:
            return results
    raise ValueError("Defender API exceeded the pagination limit; snapshot incomplete")


def fetch_optional(
    name: str,
    permission: str,
    fetch: Callable[[], list[dict[str, Any]]],
) -> list[dict[str, Any]] | None:
    """Return a complete collection, or None when the tenant can't provide it.

    Missing provisioning or permissions skip the collection without cleanup, like
    optional Entra datasets. Any other failure propagates.
    """
    try:
        return fetch()
    except ClientAuthenticationError as e:
        if RESOURCE_NOT_PROVISIONED not in str(e):
            raise
        logger.info(
            "Defender for Endpoint is not provisioned in this tenant; skipping "
            "Defender %s.",
            name,
        )
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        if status in (401, 403):
            logger.warning(
                "Defender %s request was denied (%d). Grant the %s application "
                "permission to sync them. Skipping; previously synced Defender "
                "%s are preserved.",
                name,
                status,
                permission,
                name,
            )
        elif status == 404 and name == "machines":
            # Microsoft documents 404 when the tenant has no recent machines.
            logger.warning(
                "Defender returned no recent machines (404). Skipping; previously "
                "synced Defender machines are preserved.",
            )
        else:
            raise
    return None


def parse_timestamps(record: dict[str, Any], fields: tuple[str, ...]) -> None:
    """Convert optional provider metadata without discarding valid inventory."""
    for field in fields:
        value = record.get(field)
        record[field] = None
        if value is None or value == "":
            continue
        try:
            # RFC 3339 allows lowercase t/z, which fromisoformat rejects.
            parsed = isoparse(value)
            if parsed.tzinfo is None:
                raise ValueError("Expected a timezone in the provider timestamp")
            record[field] = parsed
        except (TypeError, ValueError):
            logger.warning(
                "Defender record %s has invalid %s; omitting optional timestamp",
                record["id"],
                field,
            )
