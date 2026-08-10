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

    # Assert TAGGED relationships from secrets to AzureTag
    expected_tag_rels = {
        (secret_id, f"{TEST_SUBSCRIPTION_ID}|env:prod"),
    }
    actual_tag_rels = check_rels(
        neo4j_session,
        "AzureKeyVaultSecret",
        "id",
        "AzureTag",
        "id",
        "TAGGED",
    )
    assert actual_tag_rels == expected_tag_rels


@patch("cartography.intel.azure.key_vaults.get_certificates")
@patch("cartography.intel.azure.key_vaults.get_keys")
@patch("cartography.intel.azure.key_vaults.get_secrets")
@patch("cartography.intel.azure.key_vaults.get_key_vaults")
def test_secret_tag_cleanup_preserves_shared_tags(
    mock_get_vaults, mock_get_secrets, mock_get_keys, mock_get_certs, neo4j_session
):
    """
    The secret-tag cleanup must only detach stale TAGGED edges from
    AzureKeyVaultSecret. It must NOT delete AzureTag nodes, which are shared
    across resource types and scoped only by subscription.
    """
    # Arrange
    mock_get_vaults.return_value = MOCK_VAULTS
    mock_get_secrets.return_value = MOCK_SECRETS
    mock_get_keys.return_value = MOCK_KEYS
    mock_get_certs.return_value = MOCK_CERTIFICATES

    stale_tag = 1  # older than TEST_UPDATE_TAG

    # A pre-existing shared tag that belongs to another resource type, last synced
    # by a previous run (stale relative to this run's update tag).
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        MERGE (t:AzureTag{id: $tag_id})
        SET t.lastupdated = $stale_tag, t.key = 'owner', t.value = 'platform'
        MERGE (s)-[res:RESOURCE]->(t)
        SET res.lastupdated = $stale_tag
        MERGE (sa:AzureStorageAccount{id: $sa_id})
        SET sa.lastupdated = $stale_tag
        MERGE (sa)-[tagged:TAGGED]->(t)
        SET tagged.lastupdated = $stale_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
        stale_tag=stale_tag,
        tag_id=f"{TEST_SUBSCRIPTION_ID}|owner:platform",
        sa_id="/subscriptions/00-00-00-00/storageAccounts/other",
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

    # Assert: the shared tag node and the other resource's TAGGED edge survive.
    shared_tag_id = f"{TEST_SUBSCRIPTION_ID}|owner:platform"
    assert (shared_tag_id,) in check_nodes(neo4j_session, "AzureTag", ["id"])
    assert (
        "/subscriptions/00-00-00-00/storageAccounts/other",
        shared_tag_id,
    ) in check_rels(
        neo4j_session,
        "AzureStorageAccount",
        "id",
        "AzureTag",
        "id",
        "TAGGED",
    )
