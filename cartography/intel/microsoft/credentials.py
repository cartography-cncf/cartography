"""
Credential construction for the Microsoft intel modules.

Microsoft syncs normally use a service principal built from a tenant ID, client
ID, and client secret. The experimental delegated Entra mode instead uses the
current Azure CLI user. Credential construction lives here so every Entra
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
) -> TokenCredential:
    """
    Build the credential used to authenticate against Microsoft Graph.

    :param tenant_id: Microsoft Entra tenant ID
    :param client_id: Application (client) ID of the registered application
    :param client_secret: Client secret of the registered application
    :param delegated_auth: Use the current Azure CLI user instead of an application
    :return: A credential the Graph clients can authenticate with
    """
    if delegated_auth:
        if client_id or client_secret:
            raise ValueError(
                "Microsoft delegated authentication cannot be combined with "
                "application credentials",
            )
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
