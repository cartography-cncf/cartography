"""
Credential construction for the Microsoft intel modules.

Every Microsoft sync authenticates the same way: a service principal built from
a tenant ID, a client ID, and a client secret. That construction used to be
copy-pasted into each sync module; it lives here instead, so the Microsoft
modules have a single auth path the way ``cartography.intel.azure.util.credentials``
does for Azure.

Call sites import this module and call ``credentials.make_credential(...)``
rather than importing the function itself, which keeps the construction
reachable as a single attribute for tests and for anything that needs to
substitute the credential.
"""

from azure.core.credentials import TokenCredential
from azure.identity import ClientSecretCredential


def make_credential(
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> TokenCredential:
    """
    Build the credential used to authenticate against Microsoft Graph.

    :param tenant_id: Microsoft Entra tenant ID
    :param client_id: Application (client) ID of the registered application
    :param client_secret: Client secret of the registered application
    :return: A credential the Graph clients can authenticate with
    """
    return ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
