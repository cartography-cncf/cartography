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

from azure.core.credentials import TokenCredential
from azure.identity import AzureCliCredential
from azure.identity import ClientSecretCredential


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
        return AzureCliCredential(tenant_id=tenant_id)
    if not client_id or not client_secret:
        raise ValueError(
            "Microsoft application authentication requires a client ID and secret",
        )
    return ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
