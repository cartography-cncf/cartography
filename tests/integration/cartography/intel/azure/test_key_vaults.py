from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.key_vaults as key_vaults
from tests.data.azure.key_vaults import MOCK_CERTIFICATES
from tests.data.azure.key_vaults import MOCK_KEYS
from tests.data.azure.key_vaults import MOCK_SECRETS
from tests.data.azure.key_vaults import MOCK_VAULTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.key_vaults.get_certificates")
@patch("cartography.intel.azure.key_vaults.get_keys")
@patch("cartography.intel.azure.key_vaults.get_secrets")
@patch("cartography.intel.azure.key_vaults.get_key_vaults")
def test_sync_key_vaults_and_contents(
    mock_get_vaults, mock_get_secrets, mock_get_keys, mock_get_certs, neo4j_session
):
    """
    Test that we can correctly sync Key Vaults and their contents.
    """
    # Arrange
    mock_get_vaults.return_value = MOCK_VAULTS
    mock_get_secrets.return_value = MOCK_SECRETS
    mock_get_keys.return_value = MOCK_KEYS
    mock_get_certs.return_value = MOCK_CERTIFICATES

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    key_vaults.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Vaults
    expected_vaults = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.KeyVault/vaults/my-test-key-vault",
            "my-test-key-vault",
        ),
    }
    actual_vaults = check_nodes(neo4j_session, "AzureKeyVault", ["id", "name"])
    assert actual_vaults == expected_vaults

    # Assert Secrets
    expected_secrets = {
        ("https://my-test-key-vault.vault.azure.net/secrets/my-secret", "my-secret")
    }
    actual_secrets = check_nodes(neo4j_session, "AzureKeyVaultSecret", ["id", "name"])
    assert actual_secrets == expected_secrets

    # Assert Keys
    expected_keys = {
        ("https://my-test-key-vault.vault.azure.net/keys/my-key", "my-key")
    }
    actual_keys = check_nodes(neo4j_session, "AzureKeyVaultKey", ["id", "name"])
    assert actual_keys == expected_keys

    # Assert Certificates
    expected_certs = {
        ("https://my-test-key-vault.vault.azure.net/certificates/my-cert", "my-cert")
    }
    actual_certs = check_nodes(
        neo4j_session, "AzureKeyVaultCertificate", ["id", "name"]
    )
    assert actual_certs == expected_certs

    # Assert Relationships
    vault_id = MOCK_VAULTS[0]["id"]
    secret_id = MOCK_SECRETS[0]["id"]
    key_id = MOCK_KEYS[0]["id"]
    cert_id = MOCK_CERTIFICATES[0]["id"]

    # Assert CONTAINS relationships from Vault to children
    expected_contains_rels = {
        (vault_id, secret_id),
        (vault_id, key_id),
        (vault_id, cert_id),
    }
    actual_contains_rels = check_rels(
        neo4j_session,
        "AzureKeyVault",
        "id",
        "AzureKeyVaultSecret",
        "id",
        "CONTAINS",
    )
    actual_contains_rels.update(
        check_rels(
            neo4j_session,
            "AzureKeyVault",
            "id",
            "AzureKeyVaultKey",
            "id",
            "CONTAINS",
        ),
    )
    actual_contains_rels.update(
        check_rels(
            neo4j_session,
            "AzureKeyVault",
            "id",
            "AzureKeyVaultCertificate",
            "id",
            "CONTAINS",
        ),
    )
    assert actual_contains_rels == expected_contains_rels

    # Assert RESOURCE relationships from Subscription to children
    expected_resource_rels = {
        (TEST_SUBSCRIPTION_ID, secret_id),
        (TEST_SUBSCRIPTION_ID, key_id),
        (TEST_SUBSCRIPTION_ID, cert_id),
    }
    actual_resource_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureKeyVaultSecret",
        "id",
        "RESOURCE",
    )
    actual_resource_rels.update(
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureKeyVaultKey",
            "id",
            "RESOURCE",
        ),
    )
    actual_resource_rels.update(
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureKeyVaultCertificate",
            "id",
            "RESOURCE",
        ),
    )
    assert actual_resource_rels == expected_resource_rels
