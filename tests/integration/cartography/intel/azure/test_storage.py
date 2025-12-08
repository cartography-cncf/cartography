from unittest.mock import patch

import cartography.intel.azure.storage
from tests.data.azure.storage import DESCRIBE_BLOB_CONTAINERS
from tests.data.azure.storage import DESCRIBE_BLOB_SERVICES
from tests.data.azure.storage import DESCRIBE_FILE_SERVICES
from tests.data.azure.storage import DESCRIBE_FILE_SHARES
from tests.data.azure.storage import DESCRIBE_QUEUE
from tests.data.azure.storage import DESCRIBE_QUEUE_SERVICES
from tests.data.azure.storage import DESCRIBE_STORAGE_ACCOUNTS
from tests.data.azure.storage import DESCRIBE_TABLE_SERVICES
from tests.data.azure.storage import DESCRIBE_TABLES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_RESOURCE_GROUP = "TestRG"
TEST_UPDATE_TAG = 123456789
sa1 = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/testSG1"
sa2 = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/testSG2"


@patch.object(
    cartography.intel.azure.storage,
    "get_blob_containers",
    side_effect=lambda creds, sub_id, service: [
        c for c in DESCRIBE_BLOB_CONTAINERS if c["service_id"] == service["id"]
    ],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_shares",
    side_effect=lambda creds, sub_id, service: [
        s for s in DESCRIBE_FILE_SHARES if s["service_id"] == service["id"]
    ],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_tables",
    side_effect=lambda creds, sub_id, service: [
        t for t in DESCRIBE_TABLES if t["service_id"] == service["id"]
    ],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_queues",
    side_effect=lambda creds, sub_id, service: [
        q for q in DESCRIBE_QUEUE if q["service_id"] == service["id"]
    ],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_blob_services",
    side_effect=lambda creds, sub_id, account: [
        bs for bs in DESCRIBE_BLOB_SERVICES if bs["storage_account_id"] == account["id"]
    ],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_file_services",
    side_effect=lambda creds, sub_id, account: [
        fs for fs in DESCRIBE_FILE_SERVICES if fs["storage_account_id"] == account["id"]
    ],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_table_services",
    side_effect=lambda creds, sub_id, account: [
        ts
        for ts in DESCRIBE_TABLE_SERVICES
        if ts["storage_account_id"] == account["id"]
    ],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_queue_services",
    side_effect=lambda creds, sub_id, account: [
        qs
        for qs in DESCRIBE_QUEUE_SERVICES
        if qs["storage_account_id"] == account["id"]
    ],
)
@patch.object(
    cartography.intel.azure.storage,
    "get_storage_account_list",
    return_value=DESCRIBE_STORAGE_ACCOUNTS,
)
def test_sync_storage_accounts(
    mock_get_accounts,
    mock_get_queue_services,
    mock_get_table_services,
    mock_get_file_services,
    mock_get_blob_services,
    mock_get_queues,
    mock_get_tables,
    mock_get_shares,
    mock_get_blob_containers,
    neo4j_session,
):
    """
    Test that storage accounts and all nested resources sync correctly via the main sync() function.
    Tests storage accounts, queue services, queues, table services, tables, file services,
    file shares, blob services, and blob containers.
    """
    # Arrange - Create subscription
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act - Call main sync function
    cartography.intel.azure.storage.sync(
        neo4j_session,
        credentials=None,  # Mocked
        subscription_id=TEST_SUBSCRIPTION_ID,
        sync_tag=TEST_UPDATE_TAG,
        common_job_parameters={
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
        },
    )

    # Assert - Check storage accounts exist
    expected_account_nodes = {
        (sa1,),
        (sa2,),
    }
    assert (
        check_nodes(neo4j_session, "AzureStorageAccount", ["id"])
        == expected_account_nodes
    )

    # Assert - Check account-to-subscription relationships
    expected_account_rels = {
        (TEST_SUBSCRIPTION_ID, sa1),
        (TEST_SUBSCRIPTION_ID, sa2),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureStorageAccount",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_account_rels
    )

    # Assert - Check queue services exist
    expected_queue_service_nodes = {
        (sa1 + "/queueServices/QS1",),
        (sa2 + "/queueServices/QS2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureStorageQueueService", ["id"])
        == expected_queue_service_nodes
    )

    # Assert - Check account-to-queue service relationships
    expected_queue_service_rels = {
        (sa1, sa1 + "/queueServices/QS1"),
        (sa2, sa2 + "/queueServices/QS2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureStorageAccount",
            "id",
            "AzureStorageQueueService",
            "id",
            "USES",
            rel_direction_right=True,
        )
        == expected_queue_service_rels
    )

    # Assert - Check queues exist
    expected_queue_nodes = {
        (sa1 + "/queueServices/QS1/queues/queue1",),
        (sa2 + "/queueServices/QS2/queues/queue2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureStorageQueue", ["id"]) == expected_queue_nodes
    )

    # Assert - Check queue service-to-queue relationships
    expected_queue_rels = {
        (sa1 + "/queueServices/QS1", sa1 + "/queueServices/QS1/queues/queue1"),
        (sa2 + "/queueServices/QS2", sa2 + "/queueServices/QS2/queues/queue2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureStorageQueueService",
            "id",
            "AzureStorageQueue",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_queue_rels
    )

    # Assert - Check table services exist
    expected_table_service_nodes = {
        (sa1 + "/tableServices/TS1",),
        (sa2 + "/tableServices/TS2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureStorageTableService", ["id"])
        == expected_table_service_nodes
    )

    # Assert - Check account-to-table service relationships
    expected_table_service_rels = {
        (sa1, sa1 + "/tableServices/TS1"),
        (sa2, sa2 + "/tableServices/TS2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureStorageAccount",
            "id",
            "AzureStorageTableService",
            "id",
            "USES",
            rel_direction_right=True,
        )
        == expected_table_service_rels
    )

    # Assert - Check tables exist
    expected_table_nodes = {
        (sa1 + "/tableServices/TS1/tables/table1",),
        (sa2 + "/tableServices/TS2/tables/table2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureStorageTable", ["id"]) == expected_table_nodes
    )

    # Assert - Check table service-to-table relationships
    expected_table_rels = {
        (sa1 + "/tableServices/TS1", sa1 + "/tableServices/TS1/tables/table1"),
        (sa2 + "/tableServices/TS2", sa2 + "/tableServices/TS2/tables/table2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureStorageTableService",
            "id",
            "AzureStorageTable",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_table_rels
    )

    # Assert - Check file services exist
    expected_file_service_nodes = {
        (sa1 + "/fileServices/FS1",),
        (sa2 + "/fileServices/FS2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureStorageFileService", ["id"])
        == expected_file_service_nodes
    )

    # Assert - Check account-to-file service relationships
    expected_file_service_rels = {
        (sa1, sa1 + "/fileServices/FS1"),
        (sa2, sa2 + "/fileServices/FS2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureStorageAccount",
            "id",
            "AzureStorageFileService",
            "id",
            "USES",
            rel_direction_right=True,
        )
        == expected_file_service_rels
    )

    # Assert - Check file shares exist
    expected_file_share_nodes = {
        (sa1 + "/fileServices/FS1/shares/share1",),
        (sa2 + "/fileServices/FS2/shares/share2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureStorageFileShare", ["id"])
        == expected_file_share_nodes
    )

    # Assert - Check file service-to-file share relationships
    expected_file_share_rels = {
        (sa1 + "/fileServices/FS1", sa1 + "/fileServices/FS1/shares/share1"),
        (sa2 + "/fileServices/FS2", sa2 + "/fileServices/FS2/shares/share2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureStorageFileService",
            "id",
            "AzureStorageFileShare",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_file_share_rels
    )

    # Assert - Check blob services exist
    expected_blob_service_nodes = {
        (sa1 + "/blobServices/BS1",),
        (sa2 + "/blobServices/BS2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureStorageBlobService", ["id"])
        == expected_blob_service_nodes
    )

    # Assert - Check account-to-blob service relationships
    expected_blob_service_rels = {
        (sa1, sa1 + "/blobServices/BS1"),
        (sa2, sa2 + "/blobServices/BS2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureStorageAccount",
            "id",
            "AzureStorageBlobService",
            "id",
            "USES",
            rel_direction_right=True,
        )
        == expected_blob_service_rels
    )

    # Assert - Check blob containers exist
    expected_blob_container_nodes = {
        (sa1 + "/blobServices/BS1/containers/container1",),
        (sa2 + "/blobServices/BS2/containers/container2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureStorageBlobContainer", ["id"])
        == expected_blob_container_nodes
    )

    # Assert - Check blob service-to-blob container relationships
    expected_blob_container_rels = {
        (sa1 + "/blobServices/BS1", sa1 + "/blobServices/BS1/containers/container1"),
        (sa2 + "/blobServices/BS2", sa2 + "/blobServices/BS2/containers/container2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureStorageBlobService",
            "id",
            "AzureStorageBlobContainer",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_blob_container_rels
    )
