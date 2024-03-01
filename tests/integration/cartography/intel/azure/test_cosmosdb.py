from copy import deepcopy

from cartography.intel.azure import cosmosdb
from cartography.util import run_analysis_job
from tests.data.azure.cosmosdb import cors1_id
from tests.data.azure.cosmosdb import cors2_id
from tests.data.azure.cosmosdb import DESCRIBE_CASSANDRA_KEYSPACES
from tests.data.azure.cosmosdb import DESCRIBE_CASSANDRA_TABLES
from tests.data.azure.cosmosdb import DESCRIBE_DATABASE_ACCOUNTS
from tests.data.azure.cosmosdb import DESCRIBE_MONGODB_COLLECTIONS
from tests.data.azure.cosmosdb import DESCRIBE_MONGODB_DATABASES
from tests.data.azure.cosmosdb import DESCRIBE_SQL_CONTAINERS
from tests.data.azure.cosmosdb import DESCRIBE_SQL_DATABASES
from tests.data.azure.cosmosdb import DESCRIBE_TABLE_RESOURCES

TEST_SUBSCRIPTION_ID = '00-00-00-00'
TEST_RESOURCE_GROUP = 'RG'
TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = '1234'
TEST_TENANT_ID = '1234'
da1 = "/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA1"
da2 = "/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA2"
rg = "/subscriptions/00-00-00-00/resourceGroups/RG"


def test_load_database_account_data(neo4j_session):
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        da1,
        da2,
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBAccount) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_database_account_data_relationships(neo4j_session):
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

    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_SUBSCRIPTION_ID,
            da1,
        ),
        (
            TEST_SUBSCRIPTION_ID,
            da2,
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureSubscription)-[:RESOURCE]->(n2:AzureCosmosDBAccount) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_database_account_write_locations(neo4j_session):
    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_database_account_write_locations(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected_nodes = {
        da1 + '/writeLocations/' + "DA1-eastus",
        da1 + '/writeLocations/' + "DA1-centralindia",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBLocation) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_database_account_write_locations_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_database_account_write_locations(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected = {
        (
            da1, da1 + '/writeLocations/' + "DA1-eastus",
        ),
        (
            da1, da1 + '/writeLocations/' + "DA1-centralindia",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:CAN_WRITE_FROM]->(n2:AzureCosmosDBLocation) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_database_account_read_locations(neo4j_session):
    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_database_account_read_locations(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected_nodes = {
        da1 + '/readLocations/' + "DA1-eastus",
        da1 + '/readLocations/' + "DA1-centralindia",
    }

    nodes = neo4j_session.run(
        """
        MATCH (:AzureCosmosDBAccount)-[:CAN_READ_FROM]->(r:AzureCosmosDBLocation) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_database_account_read_locations_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_database_account_read_locations(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected = {
        (
            da1, da1 + '/readLocations/' + "DA1-eastus",
        ),
        (
            da1, da1 + '/readLocations/' + "DA1-centralindia",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:CAN_READ_FROM]->(n2:AzureCosmosDBLocation) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_database_account_associated_locations(neo4j_session):
    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_database_account_associated_locations(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected_nodes = {
        '/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA1/locations/DA1-centralindia',
        '/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA1/locations/DA1-eastus',
        '/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA1/locations/DA1-japaneast',
        '/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA1/readLocations/DA1-centralindia',
        '/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA1/readLocations/DA1-eastus',
        '/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA1/writeLocations/DA1-centralindia',
        '/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA1/writeLocations/DA1-eastus',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBLocation) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_database_account_associated_iprules(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )
    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_database_account_associated_iprules(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )
    expected = {
        (
            "34.34.14.01"
        ),
        (
            "56.89.88.01"
        ),

    }
    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureFirewallRule)-[:FIREWALL_RULE]->(n2:AzureCosmosDBAccount) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }
    assert actual == expected


def test_load_database_account_associated_locations_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )
    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_database_account_associated_locations(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected = {
        (
            da1, da1 + '/locations/' + "DA1-eastus",
        ),
        (
            da1, da1 + '/locations/' + "DA1-centralindia",
        ),
        (
            da1, da1 + '/locations/' + "DA1-japaneast",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:ASSOCIATED_WITH]->(n2:AzureCosmosDBLocation) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_cosmosdb_cors_policy(neo4j_session):
    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_cosmosdb_cors_policy(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected_nodes = {
        cors1_id, cors2_id,
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBCorsPolicy) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cosmosdb_cors_policy_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_cosmosdb_cors_policy(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected = {
        (
            da1, cors1_id,
        ),
        (
            da2, cors2_id,
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:CONTAINS]->(n2:AzureCosmosDBCorsPolicy) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_cosmosdb_failover_policies(neo4j_session):
    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_cosmosdb_failover_policies(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected_nodes = {
        da1 + '/failoverPolicies/DA1-eastus',
        da2 + '/failoverPolicies/DA2-eastus',
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBAccountFailoverPolicy) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cosmosdb_failover_policies_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_cosmosdb_failover_policies(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected = {
        (
            da1, da1 + '/failoverPolicies/' + "DA1-eastus",
        ),
        (
            da2, da2 + '/failoverPolicies/' + "DA2-eastus",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:CONTAINS]->(n2:AzureCosmosDBAccountFailoverPolicy) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_cosmosdb_private_endpoint_connections(neo4j_session):
    accounts = deepcopy(DESCRIBE_DATABASE_ACCOUNTS)
    for database_account in accounts:
        cosmosdb._load_cosmosdb_private_endpoint_connections(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected_nodes = {
        da1 + "/privateEndpointConnections/pe1",
        da2 + "/privateEndpointConnections/pe2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCDBPrivateEndpointConnection) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cosmosdb_private_endpoint_connections_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    for database_account in DESCRIBE_DATABASE_ACCOUNTS:
        cosmosdb._load_cosmosdb_private_endpoint_connections(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
        )

    expected = {
        (
            da1, da1 + "/privateEndpointConnections/pe1",
        ),
        (
            da2, da2 + "/privateEndpointConnections/pe2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:CONFIGURED_WITH]->(n2:AzureCDBPrivateEndpointConnection) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_cosmosdb_virtual_network_rules(neo4j_session):
    for database_account in DESCRIBE_DATABASE_ACCOUNTS:
        cosmosdb._load_cosmosdb_virtual_network_rules(
            neo4j_session=neo4j_session,
            database_account=database_account,
            azure_update_tag=TEST_UPDATE_TAG,
            common_job_parameters={'Azure_Primary_AD_Domain_Name': 'cdx'},
        )

    expected_nodes = {
        rg + "/providers/Microsoft.Network/virtualNetworks/vn1",
        rg + "/providers/Microsoft.Network/virtualNetworks/vn2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBVirtualNetworkRule) RETURN r.id;
        """,
    )

    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cosmosdb_virtual_network_rules_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    for database_account in DESCRIBE_DATABASE_ACCOUNTS:
        cosmosdb._load_cosmosdb_virtual_network_rules(
            neo4j_session,
            database_account,
            TEST_UPDATE_TAG,
            common_job_parameters={'Azure_Primary_AD_Domain_Name': '123'},
        )

    expected = {
        (
            da1, rg + "/providers/Microsoft.Network/virtualNetworks/vn1",
        ),
        (
            da2, rg + "/providers/Microsoft.Network/virtualNetworks/vn2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:CONFIGURED_WITH]->(n2:AzureCosmosDBVirtualNetworkRule) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_sql_databases(neo4j_session):
    cosmosdb._load_sql_databases(
        neo4j_session,
        DESCRIBE_SQL_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        da1 + "/sqlDatabases/sql_db1",
        da2 + "/sqlDatabases/sql_db2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBSqlDatabase) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_sql_databases_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    cosmosdb._load_sql_databases(
        neo4j_session,
        DESCRIBE_SQL_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            da1, da1 + "/sqlDatabases/sql_db1",
        ),
        (
            da2, da2 + "/sqlDatabases/sql_db2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:CONTAINS]->(n2:AzureCosmosDBSqlDatabase) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_cassandra_keyspaces(neo4j_session):
    cosmosdb._load_cassandra_keyspaces(
        neo4j_session,
        DESCRIBE_CASSANDRA_KEYSPACES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        da1 + "/cassandraKeyspaces/cass_ks1",
        da2 + "/cassandraKeyspaces/cass_ks2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBCassandraKeySpace) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cassandra_keyspaces_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    cosmosdb._load_cassandra_keyspaces(
        neo4j_session,
        DESCRIBE_CASSANDRA_KEYSPACES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            da1, da1 + "/cassandraKeyspaces/cass_ks1",
        ),
        (
            da2, da2 + "/cassandraKeyspaces/cass_ks2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:CONTAINS]->(n2:AzureCosmosDBCassandraKeySpace) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_mongodb_databases(neo4j_session):
    cosmosdb._load_mongodb_databases(
        neo4j_session,
        DESCRIBE_MONGODB_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        da1 + "/mongodbDatabases/mongo_db1",
        da2 + "/mongodbDatabases/mongo_db2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBMongoDBDatabase) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_mongodb_databases_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    cosmosdb._load_mongodb_databases(
        neo4j_session,
        DESCRIBE_MONGODB_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            da1, da1 + "/mongodbDatabases/mongo_db1",
        ),
        (
            da2, da2 + "/mongodbDatabases/mongo_db2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:CONTAINS]->(n2:AzureCosmosDBMongoDBDatabase) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_table_resources(neo4j_session):
    cosmosdb._load_table_resources(
        neo4j_session,
        DESCRIBE_TABLE_RESOURCES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        da1 + "/tables/table1",
        da2 + "/tables/table2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBTableResource) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_table_resources_relationships(neo4j_session):
    # Create Test Azure Database Account
    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        DESCRIBE_DATABASE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )

    cosmosdb._load_table_resources(
        neo4j_session,
        DESCRIBE_TABLE_RESOURCES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            da1, da1 + "/tables/table1",
        ),
        (
            da2, da2 + "/tables/table2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBAccount)-[:CONTAINS]->(n2:AzureCosmosDBTableResource) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_sql_containers(neo4j_session):
    cosmosdb._load_sql_containers(
        neo4j_session,
        DESCRIBE_SQL_CONTAINERS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        da1 + "/sqlDatabases/sql_db1/sqlContainers/con1",
        da2 + "/sqlDatabases/sql_db2/sqlContainers/con2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBSqlContainer) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_sql_containers_relationships(neo4j_session):
    # Create Test SQL Database
    cosmosdb._load_sql_databases(
        neo4j_session,
        DESCRIBE_SQL_DATABASES,
        TEST_UPDATE_TAG,
    )

    cosmosdb._load_sql_containers(
        neo4j_session,
        DESCRIBE_SQL_DATABASES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            da1 + "/sqlDatabases/sql_db1", da1 + "/sqlDatabases/sql_db1/sqlContainers/con1",
        ),
        (
            da2 + "/sqlDatabases/sql_db2", da2 + "/sqlDatabases/sql_db2/sqlContainers/con2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBSqlDatabase)-[:CONTAINS]->(n2:AzureCosmosDBSqlContainer) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_cassandra_tables(neo4j_session):
    cosmosdb._load_cassandra_tables(
        neo4j_session,
        DESCRIBE_CASSANDRA_TABLES,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        da1 + "/cassandraKeyspaces/cass_ks1/cassandraTables/table1",
        da2 + "/cassandraKeyspaces/cass_ks2/cassandraTables/table2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBCassandraTable) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_cassandra_tables_relationships(neo4j_session):
    # Create Test Cassandra Keyspace
    cosmosdb._load_cassandra_keyspaces(
        neo4j_session,
        DESCRIBE_CASSANDRA_KEYSPACES,
        TEST_UPDATE_TAG,
    )

    cosmosdb._load_cassandra_tables(
        neo4j_session,
        DESCRIBE_CASSANDRA_TABLES,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            da1 + "/cassandraKeyspaces/cass_ks1", da1 + "/cassandraKeyspaces/cass_ks1/cassandraTables/table1",
        ),
        (
            da2 + "/cassandraKeyspaces/cass_ks2", da2 + "/cassandraKeyspaces/cass_ks2/cassandraTables/table2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBCassandraKeySpace)-[:CONTAINS]->(n2:AzureCosmosDBCassandraTable) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_collections(neo4j_session):
    cosmosdb._load_collections(
        neo4j_session,
        DESCRIBE_MONGODB_COLLECTIONS,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        da1 + "/mongodbDatabases/mongo_db1/mongodbCollections/col1",
        da2 + "/mongodbDatabases/mongo_db2/mongodbCollections/col2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AzureCosmosDBMongoDBCollection) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_collections_relationships(neo4j_session):
    # Create Test MongoDB Databases
    cosmosdb._load_mongodb_databases(
        neo4j_session,
        DESCRIBE_MONGODB_DATABASES,
        TEST_UPDATE_TAG,
    )

    cosmosdb._load_collections(
        neo4j_session,
        DESCRIBE_MONGODB_COLLECTIONS,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            da1 + "/mongodbDatabases/mongo_db1", da1 + "/mongodbDatabases/mongo_db1/mongodbCollections/col1",
        ),
        (
            da2 + "/mongodbDatabases/mongo_db2", da2 + "/mongodbDatabases/mongo_db2/mongodbCollections/col2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AzureCosmosDBMongoDBDatabase)-[:CONTAINS]->(n2:AzureCosmosDBMongoDBCollection) RETURN n1.id, n2.id;
        """,
    )

    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_cosmosdb_asset_exposure(neo4j_session):

    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})<-[:RESOURCE]-(:AzureTenant{id: $AZURE_TENANT_ID})<-[:OWNER]-(:CloudanixWorkspace{id: $WORKSPACE_ID})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        AZURE_TENANT_ID=TEST_TENANT_ID,
        WORKSPACE_ID=TEST_WORKSPACE_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    data = cosmosdb.transform_database_account_data(DESCRIBE_DATABASE_ACCOUNTS)

    cosmosdb.load_database_account_data(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        data,
        TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "WORKSPACE_ID": TEST_WORKSPACE_ID,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
        "AZURE_TENANT_ID": TEST_TENANT_ID,
    }

    run_analysis_job(
        'azure_cosmosdb_asset_exposure.json',
        neo4j_session,
        common_job_parameters,
    )

    expected_nodes = {
        ('/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA2', 'public_network'),
    }

    nodes = neo4j_session.run(
        """
        MATCH (n:AzureCosmosDBAccount{exposed_internet: true}) return n.id, n.exposed_internet_type
        """,
    )

    actual_nodes = {
        (n['n.id'], ",".join(n['n.exposed_internet_type'])) for n in nodes
    }

    assert expected_nodes == actual_nodes
