from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.data_lake as data_lake
from tests.data.azure.data_lake import MOCK_FILESYSTEMS
from tests.data.azure.data_lake import MOCK_STORAGE_ACCOUNTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789
TEST_STORAGE_ACCOUNT_ID = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/datalakeaccount"


@patch("cartography.intel.azure.data_lake.get_filesystems_for_account")
@patch("cartography.intel.azure.data_lake.get_datalake_accounts")
def test_sync_datalake_filesystems(
    mock_get_accounts, mock_get_filesystems, neo4j_session
):
    """
    Test that we can correctly sync Data Lake File System data and relationships.
    """
    # Arrange
    mock_get_accounts.return_value = MOCK_STORAGE_ACCOUNTS
    mock_get_filesystems.return_value = MOCK_FILESYSTEMS

    # Create the prerequisite AzureSubscription and AzureStorageAccount nodes
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (sa:AzureStorageAccount{id: $sa_id})
        SET sa.lastupdated = $update_tag
        """,
        sa_id=TEST_STORAGE_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    data_lake.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes
    expected_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/datalakeaccount/blobServices/default/containers/filesystem1",
            "filesystem1",
        ),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureDataLakeFileSystem", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert Relationships - Legacy CONTAINS relationship to StorageAccount
    expected_contains_rels = {
        (
            TEST_STORAGE_ACCOUNT_ID,
            MOCK_FILESYSTEMS[0]["id"],
        ),
    }
    actual_contains_rels = check_rels(
        neo4j_session,
        "AzureStorageAccount",
        "id",
        "AzureDataLakeFileSystem",
        "id",
        "CONTAINS",
    )
    assert actual_contains_rels == expected_contains_rels

    # Assert Relationships - New RESOURCE relationship to Subscription
    expected_resource_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            MOCK_FILESYSTEMS[0]["id"],
        ),
    }
    actual_resource_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureDataLakeFileSystem",
        "id",
        "RESOURCE",
    )
    assert actual_resource_rels == expected_resource_rels


def test_load_datalake_tags(neo4j_session):
    """
    Test that tags are correctly loaded for Data Lake accounts.
    """
    # 1. Arrange
    neo4j_session.run(
        """
        MERGE (sa:AzureStorageAccount{id: $sa_id})
        SET sa.lastupdated = $update_tag
        """,
        sa_id=MOCK_STORAGE_ACCOUNTS[0]["id"],
        update_tag=TEST_UPDATE_TAG,
    )

    # 2. Act
    data_lake.load_datalake_tags(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        MOCK_STORAGE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    # 3. Assert: Check for tags
    expected_tags = {
        f"{TEST_SUBSCRIPTION_ID}|env:prod",
        f"{TEST_SUBSCRIPTION_ID}|service:datalake",
        f"{TEST_SUBSCRIPTION_ID}|service:standard-storage",
    }
    tag_nodes = neo4j_session.run("MATCH (t:AzureTag) RETURN t.id")
    actual_tags = {n["t.id"] for n in tag_nodes}
    assert actual_tags == expected_tags

    # 4. Assert: Check the relationship for the Data Lake account
    result = neo4j_session.run(
        """
        MATCH (sa:AzureStorageAccount{id: $sa_id})-[:TAGGED]->(t:AzureTag)
        RETURN t.id
        """,
        sa_id=MOCK_STORAGE_ACCOUNTS[0]["id"],
    )
    actual_rels = {r["t.id"] for r in result}
    expected_rels = {
        f"{TEST_SUBSCRIPTION_ID}|env:prod",
        f"{TEST_SUBSCRIPTION_ID}|service:datalake",
    }
    assert actual_rels == expected_rels
