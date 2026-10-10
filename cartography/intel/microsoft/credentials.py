"""
Credential construction for the Microsoft intel modules.

Microsoft syncs normally use a service principal built from a tenant ID, client
ID, and client secret. The experimental delegated Entra mode instead uses the
current Azure CLI user, or a pre-issued Microsoft Graph access token. Credential construction lives here so every Entra
dataset follows the selected authentication mode consistently.

Call sites import this module and call ``credentials.make_credential(...)``
rather than importing the function itself, which keeps the construction
reachable as a single attribute for tests and for anything that needs to
substitute the credential.
"""

import threading
import time
from typing import Any

from azure.core.credentials import AccessToken
from azure.core.credentials import TokenCredential
from azure.identity import AzureCliCredential
from azure.identity import ClientSecretCredential

from cartography.intel.common.access_token import make_static_credential
from cartography.intel.common.access_token import MICROSOFT_GRAPH


class CachingTokenCredential:
    """Cache tokens from a credential that does not cache them itself."""

    def __init__(self, credential: TokenCredential) -> None:
        self._credential = credential
        self._tokens: dict[tuple[str, ...], AccessToken] = {}
        self._lock = threading.Lock()

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        # A claims challenge requires a new token containing those claims. A
        # scope-only cache entry cannot satisfy that request safely.
        if kwargs.get("claims"):
            return self._credential.get_token(*scopes, **kwargs)

        key = tuple(scopes)
        with self._lock:
            token = self._tokens.get(key)
            if token is None or token.expires_on <= time.time() + 300:
                token = self._credential.get_token(*scopes, **kwargs)
                self._tokens[key] = token
            return token


def make_credential(
    tenant_id: str,
    client_id: str | None,
    client_secret: str | None,
    *,
    delegated_auth: bool = False,
    access_token: str | None = None,
) -> TokenCredential:
    """
    Build the credential used to authenticate against Microsoft Graph.

    :param tenant_id: Microsoft Entra tenant ID
    :param client_id: Application (client) ID of the registered application
    :param client_secret: Client secret of the registered application
    :param delegated_auth: Use a user's identity instead of an application
    :param access_token: A pre-issued Graph access token for delegated auth; the
        current Azure CLI user is used when it is not set
    :return: A credential the Graph clients can authenticate with
    """
    if access_token and not delegated_auth:
        raise ValueError("A Microsoft access token requires delegated authentication")
    if delegated_auth:
        if client_id or client_secret:
            raise ValueError(
                "Microsoft delegated authentication cannot be combined with "
                "application credentials",
            )
        if access_token:
            credential, claims = make_static_credential(access_token, MICROSOFT_GRAPH)
            if claims.tenant_id != tenant_id:
                raise ValueError(
                    "The Microsoft access token belongs to a different tenant "
                    "than the configured Microsoft tenant ID",
                )
            return credential
        return CachingTokenCredential(AzureCliCredential(tenant_id=tenant_id))
    if not client_id or not client_secret:
        raise ValueError(
            "Microsoft application authentication requires a client ID and secret",
        )
    return ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
