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

    # Assert Relationships
    expected_rels = {
        (
            TEST_STORAGE_ACCOUNT_ID,
            MOCK_FILESYSTEMS[0]["id"],
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureStorageAccount",
        "id",
        "AzureDataLakeFileSystem",
        "id",
        "CONTAINS",
    )
    assert actual_rels == expected_rels
