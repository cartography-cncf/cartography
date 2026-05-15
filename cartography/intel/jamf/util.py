import logging
from typing import Any
from typing import NoReturn

import requests
import requests.auth

from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)
_CLASSIC_API_PATH = "/JSSResource"
_AUTH_TOKEN_PATH = "/api/v1/auth/token"
_DEFAULT_PAGE_SIZE = 100


def _normalize_jamf_base_uri(jamf_base_uri: str) -> str:
    return jamf_base_uri.rstrip("/")


def _get_jamf_instance_uri(jamf_base_uri: str) -> str:
    normalized_uri = _normalize_jamf_base_uri(jamf_base_uri)
    if normalized_uri.endswith(_CLASSIC_API_PATH):
        return normalized_uri[: -len(_CLASSIC_API_PATH)]
    return normalized_uri


def _get_request_base_uri(jamf_base_uri: str, api_path: str) -> str:
    normalized_uri = _normalize_jamf_base_uri(jamf_base_uri)
    if api_path.startswith("/api/"):
        return _get_jamf_instance_uri(normalized_uri)
    if normalized_uri.endswith(_CLASSIC_API_PATH):
        return normalized_uri
    return f"{normalized_uri}{_CLASSIC_API_PATH}"


def get_http_status_code(err: requests.HTTPError) -> int | None:
    if err.response is None:
        return None
    return err.response.status_code


def normalize_group_id(value: Any) -> int | str | None:
    # Jamf's modern APIs return numeric group IDs as strings, while the Classic API
    # fallback returns ints. Normalize both to ints for stable node matching.
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def _raise_http_status(response: requests.Response) -> NoReturn:
    response.raise_for_status()
    raise RuntimeError("requests.Response.raise_for_status() unexpectedly returned")


@timeit
def create_jamf_api_session(
    jamf_base_uri: str,
    jamf_user: str,
    jamf_password: str,
) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    jamf_auth = requests.auth.HTTPBasicAuth(jamf_user, jamf_password)
    token_uri = f"{_get_jamf_instance_uri(jamf_base_uri)}{_AUTH_TOKEN_PATH}"
    try:
        response = session.post(
            token_uri,
            auth=jamf_auth,
            timeout=_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        logger.warning("Jamf: requests.post('%s') timed out.", token_uri)
        session.close()
        raise

    if response.ok:
        # TODO: Jamf bearer tokens expire after a short TTL. Refresh or keep alive the
        # token if this sync grows enough for long-running sessions to matter.
        session.headers.update(
            {"Authorization": f"Bearer {response.json()['token']}"},
        )
        logger.info("Jamf: authenticated to the Classic API using bearer token auth.")
        return session

    if response.status_code in {404, 405}:
        session.auth = jamf_auth
        logger.info(
            "Jamf: auth token endpoint unavailable at '%s'; falling back to legacy Basic auth.",
            token_uri,
        )
        return session

    try:
        _raise_http_status(response)
    except requests.HTTPError:
        session.close()
        raise


@timeit
def call_jamf_api(
    api_and_parameters: str,
    jamf_base_uri: str,
    api_session: requests.Session,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    uri = _get_request_base_uri(jamf_base_uri, api_and_parameters) + api_and_parameters
    try:
        response = api_session.get(
            uri,
            timeout=_TIMEOUT,
            params=params,
        )
    except requests.exceptions.Timeout:
        # Add context and re-raise for callers to handle
        logger.warning("Jamf: requests.get('%s') timed out.", uri)
        raise
    # if call failed, use requests library to raise an exception
    response.raise_for_status()
    return response.json()


@timeit
def get_paginated_jamf_results(
    api_path: str,
    jamf_base_uri: str,
    api_session: requests.Session,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    page = 0
    results: list[dict[str, Any]] = []

    while True:
        page_params = {"page": page, "page-size": _DEFAULT_PAGE_SIZE}
        if params:
            page_params.update(params)

        response = call_jamf_api(
            api_path,
            jamf_base_uri,
            api_session,
            params=page_params,
        )
        page_results = response.get("results", [])
        results.extend(page_results)

        total_count = response.get("totalCount")
        if total_count is None or len(results) >= total_count or not page_results:
            return results

        page += 1
