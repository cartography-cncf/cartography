from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.azure.util.credentials import Authenticator

TEST_SUBSCRIPTION_ID = "00000000-0000-0000-0000-000000000000"
TEST_TENANT_ID = "00000000-0000-0000-0000-000000000001"
# A fake JWT token string for testing.
TEST_TOKEN = "fake-header.eyJ0aWQiOiAiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAxIn0=.fake-signature"


@patch("cartography.intel.azure.util.credentials._get_tenant_id_from_token")
@patch("cartography.intel.azure.util.credentials.SubscriptionClient")
@patch("cartography.intel.azure.util.credentials.AzureCliCredential")
def test_authenticate_cli_success(
    mock_cli_credential, mock_subscription_client, mock_get_tenant
):
    """
    Test that authenticate_cli returns a valid Credentials object on success.
    """
    # Arrange
    mock_sub = MagicMock()
    mock_sub.subscription_id = TEST_SUBSCRIPTION_ID

    mock_sub_client_instance = mock_subscription_client.return_value
    mock_sub_client_instance.subscriptions.list.return_value = iter([mock_sub])

    mock_get_tenant.return_value = TEST_TENANT_ID

    # Act
    authenticator = Authenticator()
    credentials = authenticator.authenticate_cli()

    # Assert
    assert credentials is not None
    assert credentials.subscription_id == TEST_SUBSCRIPTION_ID
    assert credentials.tenant_id == TEST_TENANT_ID
    assert credentials.credential == mock_cli_credential.return_value


@patch("cartography.intel.azure.util.credentials.AzureCliCredential")
def test_authenticate_cli_failure(mock_cli_credential):
    """
    Test that authenticate_cli returns None when an exception occurs.
    """
    # Arrange: Configure the mock to raise an exception when an instance is created.
    mock_cli_credential.side_effect = Exception("Simulated authentication error")

    # Act
    authenticator = Authenticator()
    credentials = authenticator.authenticate_cli()

    # Assert
    assert credentials is None
