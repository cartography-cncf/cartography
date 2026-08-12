from typing import Any
from urllib.parse import parse_qsl
from urllib.parse import urljoin
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

DEFAULT_BASE_URL = "https://api.snyk.io/rest"
SNYK_API_VERSION = "2024-10-15"
TIMEOUT = (60, 60)


def build_session(api_key: str) -> requests.Session:
    session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.headers.update(
        {
            "Authorization": f"token {api_key}",
            "Content-Type": "application/vnd.api+json",
        }
    )
    return session


def _absolute_next_url(base_url: str, next_link: str | None) -> str | None:
    if not next_link:
        return None
    parsed = urlparse(next_link)
    if parsed.scheme and parsed.netloc:
        return next_link
    return urljoin(base_url, next_link)


def _with_version(url: str) -> str:
    parsed = urlparse(url)
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    if any(key == "version" for key, _value in query_params):
        return url
    return urlunparse(
        parsed._replace(query=urlencode([*query_params, ("version", SNYK_API_VERSION)]))
    )


def get_jsonapi_resource(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = {"version": SNYK_API_VERSION}
    request_params.update(params or {})
    response = session.get(url, params=request_params, timeout=TIMEOUT)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ValueError(
            f"Snyk API returned a non-object response for {url}: {type(body)}."
        )
    data = body.get("data")
    if not isinstance(data, dict):
        raise ValueError(
            f"Snyk API returned malformed resource for {url}: expected object data."
        )
    return data


def list_jsonapi_resources(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_url: str | None = url
    request_params: dict[str, Any] | None = {"version": SNYK_API_VERSION}
    request_params.update(params or {})

    while next_url:
        current_url = next_url
        response = session.get(current_url, params=request_params, timeout=TIMEOUT)
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise ValueError(
                f"Snyk API returned a non-object response for {current_url}: {type(body)}."
            )
        data = body.get("data")
        if not isinstance(data, list):
            raise ValueError(
                f"Snyk API returned malformed collection for {next_url}: expected list data."
            )
        for item in data:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Snyk API returned malformed collection item for {next_url}: {item!r}."
                )
        items.extend(data)

        links = body.get("links", {})
        if not isinstance(links, dict):
            raise ValueError(
                f"Snyk API returned malformed links for {next_url}: expected object."
            )
        next_url = _absolute_next_url(current_url, links.get("next"))
        if next_url:
            next_url = _with_version(next_url)
        request_params = None

    return items


def attributes(resource: dict[str, Any]) -> dict[str, Any]:
    value = resource.get("attributes") or {}
    if not isinstance(value, dict):
        raise ValueError(
            f"Snyk resource {resource.get('id')} has non-object attributes."
        )
    return value


def relationship_id(resource: dict[str, Any], relationship_name: str) -> str | None:
    relationships = resource.get("relationships") or {}
    if not isinstance(relationships, dict):
        raise ValueError(
            f"Snyk resource {resource.get('id')} has non-object relationships."
        )
    relationship = relationships.get(relationship_name) or {}
    if not isinstance(relationship, dict):
        raise ValueError(
            f"Snyk resource {resource.get('id')} has malformed {relationship_name} relationship."
        )
    data = relationship.get("data")
    if data is None:
        return None
    if isinstance(data, dict):
        rel_id = data.get("id")
        if rel_id is None:
            return None
        if not isinstance(rel_id, str):
            raise ValueError(
                f"Snyk resource {resource.get('id')} has non-string {relationship_name} id."
            )
        return rel_id
    if isinstance(data, list):
        return None
    raise ValueError(
        f"Snyk resource {resource.get('id')} has unsupported {relationship_name} relationship data."
    )


def require_id(resource: dict[str, Any], resource_name: str) -> str:
    value = resource.get("id")
    if not isinstance(value, str) or not value:
        raise ValueError(f"Snyk {resource_name} is missing required id.")
    return value
