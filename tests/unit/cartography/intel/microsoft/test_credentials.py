from unittest.mock import patch

import pytest
from azure.identity import ClientSecretCredential

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


@patch("cartography.intel.microsoft.credentials.AzureCliCredential")
def test_make_credential_uses_azure_cli_for_delegated_auth(
    mock_azure_cli_credential,
) -> None:
    # Act
    credential = credentials.make_credential(
        "tenant-id",
        None,
        None,
        delegated_auth=True,
    )

    # Assert
    mock_azure_cli_credential.assert_called_once_with(tenant_id="tenant-id")
    assert credential is mock_azure_cli_credential.return_value


def test_make_credential_requires_application_credentials() -> None:
    # Act and assert
    with pytest.raises(ValueError, match="requires a client ID and secret"):
        credentials.make_credential("tenant-id", None, None)


def test_make_credential_rejects_mixed_authentication_modes() -> None:
    # Act and assert
    with pytest.raises(ValueError, match="cannot be combined"):
        credentials.make_credential(
            "tenant-id",
            "client-id",
            "client-secret",
            delegated_auth=True,
        )
