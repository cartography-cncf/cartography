from cartography.intel.azure import storage
from tests.data.azure.storage import DESCRIBE_BLOB_CONTAINERS
from tests.data.azure.storage import DESCRIBE_BLOB_SERVICES
from tests.data.azure.storage import DESCRIBE_FILE_SERVICES
from tests.data.azure.storage import DESCRIBE_FILE_SHARES
from tests.data.azure.storage import DESCRIBE_QUEUE
from tests.data.azure.storage import DESCRIBE_QUEUE_SERVICES
from tests.data.azure.storage import DESCRIBE_STORAGE_ACCOUNTS
from tests.data.azure.storage import DESCRIBE_TABLE_SERVICES
from tests.data.azure.storage import DESCRIBE_TABLES

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_RESOURCE_GROUP = "TestRG"
TEST_UPDATE_TAG = 123456789
sa1 = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/testSG1"
sa2 = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/testSG2"


def test_load_storage_account_data(neo4j_session):
    storage.load_storage_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_STORAGE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        sa1,
        sa2,
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureStorageAccount) RETURN r.id;
        """,
    )
    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_storage_account_data_relationships(neo4j_session):
    # Create Test Azure Subscription
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    storage.load_storage_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_STORAGE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            sa1,
        ),
        (
            TEST_SUBSCRIPTION_ID,
            sa2,
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureStorageAccount) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


def test_load_queue_services(neo4j_session):
    storage._load_queue_services(
        neo4j_session,
        DESCRIBE_QUEUE_SERVICES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        sa1 + "/queueServices/QS1",
        sa2 + "/queueServices/QS2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureStorageQueueService) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_queue_services_relationships(neo4j_session):
    # Create Test Azure Storage Account
    storage.load_storage_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_STORAGE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    storage._load_queue_services(
        neo4j_session,
        DESCRIBE_QUEUE_SERVICES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            sa1,
            sa1 + "/queueServices/QS1",
        ),
        (
            sa2,
            sa2 + "/queueServices/QS2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureStorageAccount)-[:USES]->(n2:AzureStorageQueueService) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


def test_load_table_services(neo4j_session):
    storage._load_table_services(
        neo4j_session,
        DESCRIBE_TABLE_SERVICES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        sa1 + "/tableServices/TS1",
        sa2 + "/tableServices/TS2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureStorageTableService) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_table_services_relationships(neo4j_session):
    # Create Test Azure Storage Account
    storage.load_storage_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_STORAGE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    storage._load_table_services(
        neo4j_session,
        DESCRIBE_TABLE_SERVICES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            sa1,
            sa1 + "/tableServices/TS1",
        ),
        (
            sa2,
            sa2 + "/tableServices/TS2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureStorageAccount)-[:USES]->(n2:AzureStorageTableService) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


def test_load_file_services(neo4j_session):
    storage._load_file_services(
        neo4j_session,
        DESCRIBE_FILE_SERVICES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        sa1 + "/fileServices/FS1",
        sa2 + "/fileServices/FS2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureStorageFileService) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_file_services_relationships(neo4j_session):
    # Create Test Azure Storage Account
    storage.load_storage_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_STORAGE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    storage._load_file_services(
        neo4j_session,
        DESCRIBE_FILE_SERVICES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            sa1,
            sa1 + "/fileServices/FS1",
        ),
        (
            sa2,
            sa2 + "/fileServices/FS2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureStorageAccount)-[:USES]->(n2:AzureStorageFileService) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


def test_load_blob_services(neo4j_session):
    storage._load_blob_services(
        neo4j_session,
        DESCRIBE_BLOB_SERVICES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        sa1 + "/blobServices/BS1",
        sa2 + "/blobServices/BS2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureStorageBlobService) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_blob_services_relationships(neo4j_session):
    # Create Test Azure Storage Account
    storage.load_storage_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_STORAGE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    storage._load_blob_services(
        neo4j_session,
        DESCRIBE_BLOB_SERVICES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            sa1,
            sa1 + "/blobServices/BS1",
        ),
        (
            sa2,
            sa2 + "/blobServices/BS2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureStorageAccount)-[:USES]->(n2:AzureStorageBlobService) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


def test_load_queues(neo4j_session):
    storage._load_queues(
        neo4j_session,
        DESCRIBE_QUEUE,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        sa1 + "/queueServices/QS1/queues/queue1",
        sa2 + "/queueServices/QS2/queues/queue2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureStorageQueue) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_queues_relationships(neo4j_session):
    # Create Test Azure Storage Queue Service
    storage._load_queue_services(
        neo4j_session,
        DESCRIBE_QUEUE_SERVICES,
        TEST_UPDATE_TAG,
    )

    storage._load_queues(
        neo4j_session,
        DESCRIBE_QUEUE,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            sa1 + "/queueServices/QS1",
            sa1 + "/queueServices/QS1/queues/queue1",
        ),
        (
            sa2 + "/queueServices/QS2",
            sa2 + "/queueServices/QS2/queues/queue2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureStorageQueueService)-[:CONTAINS]->(n2:AzureStorageQueue) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


def test_load_tables(neo4j_session):
    storage._load_tables(
        neo4j_session,
        DESCRIBE_TABLES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        sa1 + "/tableServices/TS1/tables/table1",
        sa2 + "/tableServices/TS2/tables/table2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureStorageTable) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_tables_relationships(neo4j_session):
    # Create Test Azure Storage Table Service
    storage._load_table_services(
        neo4j_session,
        DESCRIBE_TABLE_SERVICES,
        TEST_UPDATE_TAG,
    )

    storage._load_tables(
        neo4j_session,
        DESCRIBE_TABLES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            sa1 + "/tableServices/TS1",
            sa1 + "/tableServices/TS1/tables/table1",
        ),
        (
            sa2 + "/tableServices/TS2",
            sa2 + "/tableServices/TS2/tables/table2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureStorageTableService)-[:CONTAINS]->(n2:AzureStorageTable) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


def test_load_shares(neo4j_session):
    storage._load_shares(
        neo4j_session,
        DESCRIBE_FILE_SHARES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        sa1 + "/fileServices/FS1/shares/share1",
        sa2 + "/fileServices/FS2/shares/share2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureStorageFileShare) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_shares_relationships(neo4j_session):
    # Create Test Azure Storage File Service
    storage._load_file_services(
        neo4j_session,
        DESCRIBE_FILE_SERVICES,
        TEST_UPDATE_TAG,
    )

    storage._load_shares(
        neo4j_session,
        DESCRIBE_FILE_SHARES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            sa1 + "/fileServices/FS1",
            sa1 + "/fileServices/FS1/shares/share1",
        ),
        (
            sa2 + "/fileServices/FS2",
            sa2 + "/fileServices/FS2/shares/share2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureStorageFileService)-[:CONTAINS]->(n2:AzureStorageFileShare) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


def test_load_blob_containers(neo4j_session):
    storage._load_blob_containers(
        neo4j_session,
        DESCRIBE_BLOB_CONTAINERS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        sa1 + "/blobServices/BS1/containers/container1",
        sa2 + "/blobServices/BS2/containers/container2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureStorageBlobContainer) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_blob_containers_relationships(neo4j_session):
    # Create Test Azure Storage Blob Service
    storage._load_blob_services(
        neo4j_session,
        DESCRIBE_BLOB_SERVICES,
        TEST_UPDATE_TAG,
    )

    storage._load_blob_containers(
        neo4j_session,
        DESCRIBE_BLOB_CONTAINERS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            sa1 + "/blobServices/BS1",
            sa1 + "/blobServices/BS1/containers/container1",
        ),
        (
            sa2 + "/blobServices/BS2",
            sa2 + "/blobServices/BS2/containers/container2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureStorageBlobService)-[:CONTAINS]->(n2:AzureStorageBlobContainer) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected
