"""
Static Microsoft identity platform access tokens.

Azure Resource Manager and Microsoft Graph syncs can both run with a token
issued elsewhere, typically a signed-in user's delegated token. A bearer token
is valid only for the audience it was issued for and cannot be refreshed, so
the credential here serves that one audience until the token expires.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import jwt
from azure.core.credentials import AccessToken
from azure.core.exceptions import ClientAuthenticationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TokenAudience:
    name: str
    # Scheme and host only; scopes such as ``<resource>/.default`` match on these.
    resources: frozenset[str]
    app_id: str

    def accepts(self, audience: str) -> bool:
        return audience == self.app_id or _resource_of(audience) in self.resources


# ARM accepts tokens for either of its resource URIs, and some management SDKs
# still request the legacy one.
AZURE_RESOURCE_MANAGER = TokenAudience(
    name="Azure Resource Manager",
    resources=frozenset(
        {"https://management.azure.com", "https://management.core.windows.net"},
    ),
    app_id="797f4846-ba00-4fd7-ba43-dac1f8f63013",
)
MICROSOFT_GRAPH = TokenAudience(
    name="Microsoft Graph",
    resources=frozenset({"https://graph.microsoft.com"}),
    app_id="00000003-0000-0000-c000-000000000000",
)


class UnsupportedTokenScopeError(ClientAuthenticationError):
    """
    Raised when a static access token is asked for an audience it was not issued
    for, such as the Key Vault data plane. Callers can catch it to skip a
    data-plane sync without masking genuine authentication failures.
    """


@dataclass(frozen=True)
class AccessTokenClaims:
    tenant_id: str
    expires_on: int


def _resource_of(value: str) -> str:
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return value
    return f"{parsed.scheme}://{parsed.netloc}".lower()


def parse_access_token(access_token: str, audience: TokenAudience) -> AccessTokenClaims:
    """
    Validate an access token's audience, tenant and expiry before any API call,
    so a token for the wrong API or an expired token fails with a clear message
    instead of a generic 401. The signature is not verified: the API verifies it.
    """
    try:
        claims = jwt.decode(access_token, options={"verify_signature": False})
    except jwt.PyJWTError as e:
        raise ValueError("The access token is not a valid JWT.") from e

    token_audience = claims.get("aud")
    token_audiences = (
        token_audience if isinstance(token_audience, list) else [token_audience]
    )
    if not any(isinstance(a, str) and audience.accepts(a) for a in token_audiences):
        raise ValueError(
            f"The access token was not issued for {audience.name} "
            f"(audience: {token_audience!r}). Request a token for "
            f"{min(audience.resources)}.",
        )

    tenant_id = claims.get("tid")
    if not tenant_id:
        raise ValueError("The access token has no tenant ID (tid) claim.")

    expires_on = claims.get("exp")
    if not isinstance(expires_on, int) or expires_on <= time.time():
        raise ValueError("The access token is expired or has no expiry (exp) claim.")
    return AccessTokenClaims(tenant_id=tenant_id, expires_on=expires_on)


class StaticAccessTokenCredential:
    """
    A ``TokenCredential`` that serves one pre-issued access token for a single
    audience. It cannot refresh the token, so a sync must finish before the token
    expires.
    """

    def __init__(
        self,
        token: str,
        expires_on: int,
        audience: TokenAudience,
    ) -> None:
        self._token = AccessToken(token, expires_on)
        self._audience = audience

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        unsupported = [scope for scope in scopes if not self._audience.accepts(scope)]
        if unsupported:
            raise UnsupportedTokenScopeError(
                f"The access token was issued for {self._audience.name} and "
                f"cannot be used for {', '.join(unsupported)}.",
            )
        if self._token.expires_on <= time.time():
            raise ClientAuthenticationError(
                "The access token expired during the sync. Issue a new token "
                "and run the sync again.",
            )
        return self._token


def log_token_lifetime(audience: TokenAudience, claims: AccessTokenClaims) -> None:
    logger.info(
        "Using a static %s access token; it expires in %d minutes and cannot be "
        "refreshed.",
        audience.name,
        (claims.expires_on - int(time.time())) // 60,
    )


def make_static_credential(
    access_token: str,
    audience: TokenAudience,
) -> tuple[StaticAccessTokenCredential, AccessTokenClaims]:
    claims = parse_access_token(access_token, audience)
    return (
        StaticAccessTokenCredential(access_token, claims.expires_on, audience),
        claims,
    )
