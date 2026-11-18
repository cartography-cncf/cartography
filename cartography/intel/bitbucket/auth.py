"""
Bitbucket Cloud authentication.

Supports the two currently-live Bitbucket Cloud auth methods. App passwords are
not supported: Atlassian stopped issuing them in 2025 and fully removed them
in mid-2026.
"""

import logging
import time

import requests

logger = logging.getLogger(__name__)

_OAUTH_TOKEN_URL = "https://bitbucket.org/site/oauth2/access_token"
_TOKEN_REFRESH_BUFFER_SECONDS = 60
_TIMEOUT = (60, 60)


class BitbucketCredential:
    """Base class for Bitbucket Cloud authentication credentials."""

    def get_token(self) -> str:
        """Return a valid bearer token string."""
        raise NotImplementedError


class BearerTokenCredential(BitbucketCredential):
    """A static Bitbucket API token or a repository/project/workspace Access token."""

    def __init__(self, token: str) -> None:
        self._token = token

    def get_token(self) -> str:
        return self._token


class OAuth2RefreshCredential(BitbucketCredential):
    """
    OAuth consumer credential using the refresh_token grant.

    Bitbucket Cloud has no client_credentials grant, so this assumes an operator
    has already completed the one-time Authorization Code consent out-of-band and
    supplied the resulting refresh token.
    """

    def __init__(self, client_id: str, client_secret: str, refresh_token: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._token: str | None = None
        self._token_expires_at: float = 0

    def get_token(self) -> str:
        if self._token is None or self._is_near_expiry():
            self._refresh_token_value()
        assert self._token is not None
        return self._token

    def _is_near_expiry(self) -> bool:
        return time.time() >= (self._token_expires_at - _TOKEN_REFRESH_BUFFER_SECONDS)

    def _refresh_token_value(self) -> None:
        logger.debug("Refreshing Bitbucket OAuth access token")
        response = requests.post(
            _OAUTH_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
            auth=(self._client_id, self._client_secret),
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        # Bitbucket may return a new refresh token; use it for later refreshes.
        self._refresh_token = data.get("refresh_token", self._refresh_token)
        self._token_expires_at = time.time() + data.get("expires_in", 7200)


def make_credential(
    auth_method: str,
    token: str | None,
    oauth_client_id: str | None,
    oauth_client_secret: str | None,
    oauth_refresh_token: str | None,
) -> BitbucketCredential:
    """Build the configured Bitbucket credential."""
    if auth_method not in ("token", "oauth"):
        raise ValueError(
            f"Unsupported bitbucket_auth_method {auth_method!r}; use 'token' or 'oauth'.",
        )
    if auth_method == "oauth":
        if not all([oauth_client_id, oauth_client_secret, oauth_refresh_token]):
            raise ValueError(
                "bitbucket_auth_method is 'oauth' but one of oauth_client_id, "
                "oauth_client_secret, oauth_refresh_token is missing.",
            )
        assert oauth_client_id and oauth_client_secret and oauth_refresh_token
        return OAuth2RefreshCredential(
            oauth_client_id, oauth_client_secret, oauth_refresh_token
        )

    if not token:
        raise ValueError(
            "bitbucket_auth_method is 'token' but no token was provided.",
        )
    return BearerTokenCredential(token)
