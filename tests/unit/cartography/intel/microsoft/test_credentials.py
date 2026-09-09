import datetime
from unittest.mock import patch

import pytest
from azure.identity import CertificateCredential
from azure.identity import ClientSecretCredential
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from cartography.intel.microsoft import credentials


def test_make_credential_returns_service_principal_credential() -> None:
    credential = credentials.make_credential(
        "tenant-id",
        "client-id",
        "client-secret",
    )

    assert isinstance(credential, ClientSecretCredential)


@patch("cartography.intel.microsoft.credentials.ClientSecretCredential")
def test_make_credential_maps_positional_args(mock_client_secret_credential) -> None:
    # Call sites pass the three values positionally, so pin the order: swapping
    # client_id and client_secret would otherwise fail only at auth time.
    credential = credentials.make_credential(
        "tenant-id",
        "client-id",
        "client-secret",
    )

    mock_client_secret_credential.assert_called_once_with(
        tenant_id="tenant-id",
        client_id="client-id",
        client_secret="client-secret",
    )
    assert credential is mock_client_secret_credential.return_value


@patch("cartography.intel.microsoft.credentials.CertificateCredential")
def test_make_credential_with_certificate_path_builds_certificate_credential(
    mock_certificate_credential,
) -> None:
    # A certificate replaces the secret: the secret is not required and is never
    # passed on when a certificate path is given.
    credential = credentials.make_credential(
        "tenant-id",
        "client-id",
        client_certificate_path="/run/secrets/app.pem",
    )

    mock_certificate_credential.assert_called_once_with(
        tenant_id="tenant-id",
        client_id="client-id",
        certificate_path="/run/secrets/app.pem",
    )
    assert credential is mock_certificate_credential.return_value


def test_make_credential_certificate_path_returns_certificate_credential(
    tmp_path,
) -> None:
    # azure-identity parses the certificate as soon as the credential is built,
    # so this needs a real key + self-signed certificate: the same PEM bundle
    # shape (PKCS#8 private key, then the certificate) an operator would supply.
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "cartography-test")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    pem = tmp_path / "app.pem"
    pem.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        + cert.public_bytes(serialization.Encoding.PEM)
    )

    credential = credentials.make_credential(
        "tenant-id",
        "client-id",
        client_certificate_path=str(pem),
    )

    assert isinstance(credential, CertificateCredential)


def test_make_credential_requires_a_secret_or_a_certificate() -> None:
    with pytest.raises(ValueError, match="client secret or a client certificate"):
        credentials.make_credential("tenant-id", "client-id")
