from unittest.mock import patch

import cartography.intel.azure.cosmosdb
from tests.data.azure.cosmosdb import DESCRIBE_CASSANDRA_KEYSPACES
from tests.data.azure.cosmosdb import DESCRIBE_CASSANDRA_TABLES
from tests.data.azure.cosmosdb import DESCRIBE_DATABASE_ACCOUNTS
from tests.data.azure.cosmosdb import DESCRIBE_MONGODB_COLLECTIONS
from tests.data.azure.cosmosdb import DESCRIBE_MONGODB_DATABASES
from tests.data.azure.cosmosdb import DESCRIBE_SQL_CONTAINERS
from tests.data.azure.cosmosdb import DESCRIBE_SQL_DATABASES
from tests.data.azure.cosmosdb import DESCRIBE_TABLE_RESOURCES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_RESOURCE_GROUP = "RG"
TEST_UPDATE_TAG = 123456789
da1 = "/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA1"
da2 = "/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA2"


@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_mongodb_collections",
    side_effect=lambda creds, sub_id, db: [
        c for c in DESCRIBE_MONGODB_COLLECTIONS if c["database_id"] == db["id"]
    ],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_cassandra_tables",
    side_effect=lambda creds, sub_id, ks: [
        t for t in DESCRIBE_CASSANDRA_TABLES if t["keyspace_id"] == ks["id"]
    ],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_sql_containers",
    side_effect=lambda creds, sub_id, db: [
        c for c in DESCRIBE_SQL_CONTAINERS if c["database_id"] == db["id"]
    ],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_table_resources",
    side_effect=lambda creds, sub_id, account: [
        t for t in DESCRIBE_TABLE_RESOURCES if t["database_account_id"] == account["id"]
    ],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_mongodb_databases",
    side_effect=lambda creds, sub_id, account: [
        db
        for db in DESCRIBE_MONGODB_DATABASES
        if db["database_account_id"] == account["id"]
    ],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_cassandra_keyspaces",
    side_effect=lambda creds, sub_id, account: [
        ks
        for ks in DESCRIBE_CASSANDRA_KEYSPACES
        if ks["database_account_id"] == account["id"]
    ],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_sql_databases",
    side_effect=lambda creds, sub_id, account: [
        db
        for db in DESCRIBE_SQL_DATABASES
        if db["database_account_id"] == account["id"]
    ],
)
@patch.object(
    cartography.intel.azure.cosmosdb,
    "get_database_account_list",
    return_value=DESCRIBE_DATABASE_ACCOUNTS,
)
def test_sync_cosmosdb_accounts(
    mock_get_accounts,
    mock_get_sql_dbs,
    mock_get_cassandra_ks,
    mock_get_mongo_dbs,
    mock_get_tables,
    mock_get_sql_containers,
    mock_get_cassandra_tables,
    mock_get_mongo_collections,
    neo4j_session,
):
    """
    Test that CosmosDB database accounts and all nested resources sync correctly via the main sync() function.
    Tests database accounts, SQL databases, SQL containers, Cassandra keyspaces, Cassandra tables,
    MongoDB databases, MongoDB collections, and Table resources.
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
    cartography.intel.azure.cosmosdb.sync(
        neo4j_session,
        credentials=None,  # Mocked
        subscription_id=TEST_SUBSCRIPTION_ID,
        sync_tag=TEST_UPDATE_TAG,
        common_job_parameters={
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
        },
    )

    # Assert - Check database accounts exist
    expected_account_nodes = {
        (da1,),
        (da2,),
    }
    assert (
        check_nodes(neo4j_session, "AzureCosmosDBAccount", ["id"])
        == expected_account_nodes
    )

    # Assert - Check account-to-subscription relationships
    expected_account_rels = {
        (TEST_SUBSCRIPTION_ID, da1),
        (TEST_SUBSCRIPTION_ID, da2),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureCosmosDBAccount",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_account_rels
    )

    # Assert - Check SQL databases exist
    expected_sql_db_nodes = {
        (da1 + "/sqlDatabases/sql_db1",),
        (da2 + "/sqlDatabases/sql_db2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureCosmosDBSqlDatabase", ["id"])
        == expected_sql_db_nodes
    )

    # Assert - Check account-to-SQL database relationships
    expected_sql_db_rels = {
        (da1, da1 + "/sqlDatabases/sql_db1"),
        (da2, da2 + "/sqlDatabases/sql_db2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureCosmosDBAccount",
            "id",
            "AzureCosmosDBSqlDatabase",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_sql_db_rels
    )

    # Assert - Check SQL containers exist
    expected_sql_container_nodes = {
        (da1 + "/sqlDatabases/sql_db1/sqlContainers/con1",),
        (da2 + "/sqlDatabases/sql_db2/sqlContainers/con2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureCosmosDBSqlContainer", ["id"])
        == expected_sql_container_nodes
    )

    # Assert - Check SQL database-to-container relationships
    expected_sql_container_rels = {
        (
            da1 + "/sqlDatabases/sql_db1",
            da1 + "/sqlDatabases/sql_db1/sqlContainers/con1",
        ),
        (
            da2 + "/sqlDatabases/sql_db2",
            da2 + "/sqlDatabases/sql_db2/sqlContainers/con2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureCosmosDBSqlDatabase",
            "id",
            "AzureCosmosDBSqlContainer",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_sql_container_rels
    )

    # Assert - Check Cassandra keyspaces exist
    expected_cassandra_ks_nodes = {
        (da1 + "/cassandraKeyspaces/cass_ks1",),
        (da2 + "/cassandraKeyspaces/cass_ks2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureCosmosDBCassandraKeyspace", ["id"])
        == expected_cassandra_ks_nodes
    )

    # Assert - Check account-to-Cassandra keyspace relationships
    expected_cassandra_ks_rels = {
        (da1, da1 + "/cassandraKeyspaces/cass_ks1"),
        (da2, da2 + "/cassandraKeyspaces/cass_ks2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureCosmosDBAccount",
            "id",
            "AzureCosmosDBCassandraKeyspace",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_cassandra_ks_rels
    )

    # Assert - Check Cassandra tables exist
    expected_cassandra_table_nodes = {
        (da1 + "/cassandraKeyspaces/cass_ks1/cassandraTables/table1",),
        (da2 + "/cassandraKeyspaces/cass_ks2/cassandraTables/table2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureCosmosDBCassandraTable", ["id"])
        == expected_cassandra_table_nodes
    )

    # Assert - Check Cassandra keyspace-to-table relationships
    expected_cassandra_table_rels = {
        (
            da1 + "/cassandraKeyspaces/cass_ks1",
            da1 + "/cassandraKeyspaces/cass_ks1/cassandraTables/table1",
        ),
        (
            da2 + "/cassandraKeyspaces/cass_ks2",
            da2 + "/cassandraKeyspaces/cass_ks2/cassandraTables/table2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureCosmosDBCassandraKeyspace",
            "id",
            "AzureCosmosDBCassandraTable",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_cassandra_table_rels
    )

    # Assert - Check MongoDB databases exist
    expected_mongo_db_nodes = {
        (da1 + "/mongodbDatabases/mongo_db1",),
        (da2 + "/mongodbDatabases/mongo_db2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureCosmosDBMongoDBDatabase", ["id"])
        == expected_mongo_db_nodes
    )

    # Assert - Check account-to-MongoDB database relationships
    expected_mongo_db_rels = {
        (da1, da1 + "/mongodbDatabases/mongo_db1"),
        (da2, da2 + "/mongodbDatabases/mongo_db2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureCosmosDBAccount",
            "id",
            "AzureCosmosDBMongoDBDatabase",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_mongo_db_rels
    )

    # Assert - Check MongoDB collections exist
    expected_mongo_collection_nodes = {
        (da1 + "/mongodbDatabases/mongo_db1/mongodbCollections/col1",),
        (da2 + "/mongodbDatabases/mongo_db2/mongodbCollections/col2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureCosmosDBMongoDBCollection", ["id"])
        == expected_mongo_collection_nodes
    )

    # Assert - Check MongoDB database-to-collection relationships
    expected_mongo_collection_rels = {
        (
            da1 + "/mongodbDatabases/mongo_db1",
            da1 + "/mongodbDatabases/mongo_db1/mongodbCollections/col1",
        ),
        (
            da2 + "/mongodbDatabases/mongo_db2",
            da2 + "/mongodbDatabases/mongo_db2/mongodbCollections/col2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureCosmosDBMongoDBDatabase",
            "id",
            "AzureCosmosDBMongoDBCollection",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_mongo_collection_rels
    )

    # Assert - Check Table resources exist
    expected_table_nodes = {
        (da1 + "/tables/table1",),
        (da2 + "/tables/table2",),
    }
    assert (
        check_nodes(neo4j_session, "AzureCosmosDBTableResource", ["id"])
        == expected_table_nodes
    )

    # Assert - Check account-to-Table resource relationships
    expected_table_rels = {
        (da1, da1 + "/tables/table1"),
        (da2, da2 + "/tables/table2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureCosmosDBAccount",
            "id",
            "AzureCosmosDBTableResource",
            "id",
            "CONTAINS",
            rel_direction_right=True,
        )
        == expected_table_rels
    )
