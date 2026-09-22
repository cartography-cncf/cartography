import time
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from azure.core.credentials import AccessToken
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
    assert isinstance(credential, credentials.CachingTokenCredential)


def test_delegated_credential_caches_cli_token(monkeypatch) -> None:
    expires_on = 2_000_000_000
    monkeypatch.setattr(time, "time", lambda: 1_000_000_000)
    with patch(
        "cartography.intel.microsoft.credentials.AzureCliCredential"
    ) as mock_azure_cli:
        cli_credential = mock_azure_cli.return_value
        cli_credential.get_token.return_value = AccessToken(
            "token",
            expires_on,
        )
        credential = credentials.make_credential(
            "tenant-id",
            None,
            None,
            delegated_auth=True,
        )
        first = credential.get_token("https://graph.microsoft.com/.default")
        second = credential.get_token("https://graph.microsoft.com/.default")

    assert first is second
    cli_credential.get_token.assert_called_once()


def test_delegated_credential_refreshes_near_expiry(monkeypatch) -> None:
    # Arrange
    monkeypatch.setattr(time, "time", lambda: 1_000)
    cli_credential = MagicMock()
    cli_credential.get_token.side_effect = (
        AccessToken("expiring-token", 1_299),
        AccessToken("fresh-token", 2_000),
    )
    credential = credentials.CachingTokenCredential(cli_credential)

    # Act
    first = credential.get_token("scope")
    second = credential.get_token("scope")

    # Assert
    assert first.token == "expiring-token"
    assert second.token == "fresh-token"
    assert cli_credential.get_token.call_count == 2


def test_delegated_credential_caches_scopes_separately(monkeypatch) -> None:
    # Arrange
    monkeypatch.setattr(time, "time", lambda: 1_000)
    cli_credential = MagicMock()
    cli_credential.get_token.side_effect = (
        AccessToken("graph-token", 2_000),
        AccessToken("management-token", 2_000),
    )
    credential = credentials.CachingTokenCredential(cli_credential)

    # Act
    graph = credential.get_token("graph-scope")
    management = credential.get_token("management-scope")

    # Assert
    assert graph.token == "graph-token"
    assert management.token == "management-token"
    assert cli_credential.get_token.call_count == 2


def test_delegated_credential_bypasses_cache_for_claims_challenge() -> None:
    # Arrange
    cli_credential = MagicMock()
    cli_credential.get_token.side_effect = (
        AccessToken("cached-token", 2_000_000_000),
        AccessToken("claims-token", 2_000_000_000),
    )
    credential = credentials.CachingTokenCredential(cli_credential)
    credential.get_token("scope")

    # Act
    challenged = credential.get_token("scope", claims="required-claims")

    # Assert
    assert challenged.token == "claims-token"
    cli_credential.get_token.assert_called_with(
        "scope",
        claims="required-claims",
    )


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
