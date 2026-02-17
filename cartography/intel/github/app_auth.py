"""
GitHub authentication support for Personal Access Tokens and GitHub App installations.

GitHub App authentication flow:
1. Generate a JWT signed with the App's private key
2. Exchange the JWT for a short-lived installation access token
3. Use the installation token for API calls (auto-refreshes when near expiry)
"""

import logging
import time
from typing import Any

import jwt
import requests

from cartography.intel.github.util import _get_rest_api_base_url

logger = logging.getLogger(__name__)

# Installation tokens are valid for 1 hour; refresh 5 minutes before expiry
_TOKEN_REFRESH_BUFFER_SECONDS = 300
_JWT_EXPIRATION_SECONDS = 600  # 10 minutes (GitHub max)
_TIMEOUT = (60, 60)


class GitHubCredential:
    """Base class for GitHub authentication credentials."""

    def get_token(self) -> str:
        """Return a valid authentication token string."""
        raise NotImplementedError


class PatCredential(GitHubCredential):
    """Personal Access Token credential - returns a static token."""

    def __init__(self, token: str) -> None:
        self._token = token

    def get_token(self) -> str:
        return self._token


class AppCredential(GitHubCredential):
    """
    GitHub App credential with automatic token refresh.

    Generates a JWT from the app's private key, exchanges it for an installation
    access token, and transparently refreshes when the token nears expiry.
    """

    def __init__(
        self,
        client_id: str,
        private_key: str,
        installation_id: str,
        api_base_url: str = "https://api.github.com",
    ) -> None:
        self._client_id = client_id
        self._private_key = private_key
        self._installation_id = installation_id
        self._api_base_url = api_base_url
        self._token: str | None = None
        self._token_expires_at: float = 0

    def get_token(self) -> str:
        if self._token is None or self._is_near_expiry():
            self._refresh_token()
        assert self._token is not None
        return self._token

    def _is_near_expiry(self) -> bool:
        return time.time() >= (self._token_expires_at - _TOKEN_REFRESH_BUFFER_SECONDS)

    def _create_jwt(self) -> str:
        now = int(time.time())
        payload = {
            "iat": now,
            "exp": now + _JWT_EXPIRATION_SECONDS,
            "iss": self._client_id,
        }
        encoded: str = jwt.encode(payload, self._private_key, algorithm="RS256")
        return encoded

    def _refresh_token(self) -> None:
        logger.debug("Refreshing GitHub App installation token")
        encoded_jwt = self._create_jwt()
        response = requests.post(
            f"{self._api_base_url}/app/installations/{self._installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {encoded_jwt}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["token"]
        # Installation tokens expire after 1 hour
        self._token_expires_at = time.time() + 3600
        logger.debug("GitHub App installation token refreshed successfully")


def make_credential(auth_data: dict[str, Any]) -> GitHubCredential:
    """
    Create the appropriate credential from a GitHub config entry.

    PAT config: {"token": "ghp_xxx", "url": "...", "name": "..."}
    App config: {"client_id": "...", "private_key": "...", "installation_id": "...", "url": "...", "name": "..."}
    """
    if "token" in auth_data:
        return PatCredential(auth_data["token"])
    if "client_id" in auth_data:
        missing = [k for k in ("private_key", "installation_id") if k not in auth_data]
        if missing:
            raise ValueError(
                f"GitHub App config with 'client_id' is missing required keys: {', '.join(missing)}",
            )
        api_base_url = _get_rest_api_base_url(auth_data["url"])
        return AppCredential(
            client_id=auth_data["client_id"],
            private_key=auth_data["private_key"],
            installation_id=auth_data["installation_id"],
            api_base_url=api_base_url,
        )
    raise ValueError(
        "GitHub config entry must contain either 'token' (PAT) or "
        "'client_id' + 'private_key' + 'installation_id' (GitHub App)",
    )
