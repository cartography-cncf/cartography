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
from azure.identity import CertificateCredential
from azure.identity import ClientSecretCredential


def make_credential(
    tenant_id: str,
    client_id: str,
    client_secret: str | None = None,
    *,
    client_certificate_path: str | None = None,
) -> TokenCredential:
    """
    Build the credential used to authenticate against Microsoft Graph.

    The app registration authenticates with either a client secret or a
    certificate. Pass exactly one; a certificate takes precedence when both are
    given because a secret is never needed alongside it.

    :param tenant_id: Microsoft Entra tenant ID
    :param client_id: Application (client) ID of the registered application
    :param client_secret: Client secret of the registered application
    :param client_certificate_path: Path to a PEM or PKCS#12 file holding the
        registered application's private key and certificate
    :return: A credential the Graph clients can authenticate with
    :raises ValueError: if neither a client secret nor a certificate is given
    """
    if client_certificate_path:
        return CertificateCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            certificate_path=client_certificate_path,
        )
    if client_secret:
        return ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
    raise ValueError(
        "Microsoft credentials need a client secret or a client certificate path",
    )
