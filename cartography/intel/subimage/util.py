import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)


def get_access_token(client_id: str, client_secret: str, authkit_url: str) -> str:
    """Exchange WorkOS client credentials for an access token."""
    response = requests.post(
        f"{authkit_url}/oauth2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def create_api_session(access_token: str) -> requests.Session:
    """Create an API session with Bearer auth and retry policy."""
    session = requests.Session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.headers.update(
        {"Authorization": f"Bearer {access_token}"},
    )
    return session
