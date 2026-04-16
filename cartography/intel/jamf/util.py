import logging
from typing import Any

import requests
import requests.auth

from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)
_CLASSIC_API_PATH = "/JSSResource"
_AUTH_TOKEN_PATH = "/api/v1/auth/token"


def _normalize_jamf_base_uri(jamf_base_uri: str) -> str:
    return jamf_base_uri.rstrip("/")


def _get_jamf_instance_uri(jamf_base_uri: str) -> str:
    normalized_uri = _normalize_jamf_base_uri(jamf_base_uri)
    if normalized_uri.endswith(_CLASSIC_API_PATH):
        return normalized_uri[: -len(_CLASSIC_API_PATH)]
    return normalized_uri


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
        raise

    if response.ok:
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

    response.raise_for_status()
    return session


@timeit
def call_jamf_api(
    api_and_parameters: str,
    jamf_base_uri: str,
    api_session: requests.Session,
) -> dict[str, Any]:
    uri = _normalize_jamf_base_uri(jamf_base_uri) + api_and_parameters
    try:
        response = api_session.get(
            uri,
            timeout=_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        # Add context and re-raise for callers to handle
        logger.warning("Jamf: requests.get('%s') timed out.", uri)
        raise
    # if call failed, use requests library to raise an exception
    response.raise_for_status()
    return response.json()
