cors1_id = "0001"  # Sample cors policy id for testing
cors2_id = "0002"  # Sample cors policy id for testing
da1 = "/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA1"
da2 = "/subscriptions/00-00-00-00/resourceGroups/RG/providers/Microsoft.DocumentDB/databaseAccounts/DA2"
rg = "/subscriptions/00-00-00-00/resourceGroups/RG"

DESCRIBE_DATABASE_ACCOUNTS = [
    {
        "id": da1,
        "name": "DA1",
        "resourceGroup": "RG",
        "location": "West US",
        "type": "Microsoft.DocumentDB/databaseAccounts",
        "kind": "GlobalDocumentDB",
        "tags": {"env": "prod", "service": "cosmosdb"},
        "provisioning_state": "Succeeded",
        "document_endpoint": "https://ddb1.documents.azure.com:443/",
        "is_virtual_network_filter_enabled": True,
        "enable_automatic_failover": True,
        "enable_multiple_write_locations": True,
        "database_account_offer_type": "Standard",
        "disable_key_based_metadata_write_access": False,
        "enable_free_tier": False,
        "enable_analytical_storage": True,
        "consistency_policy": {
            "default_consistency_level": "Session",
            "max_interval_in_seconds": 5,
            "max_staleness_prefix": 100,
        },
        "write_locations": [
            {
                "id": "DA1-eastus",
                "location_name": "East US",
                "document_endpoint": "https://DA1-eastus.documents.azure.com:443/",
                "provisioning_state": "Succeeded",
                "failover_priority": 0,
            },
            {
                "id": "DA1-centralindia",
                "location_name": "Central India",
                "document_endpoint": "https://DA1-centralindia.documents.azure.com:443/",
                "provisioning_state": "Succeeded",
                "failover_priority": 0,
            },
        ],
        "read_locations": [
            {
                "id": "DA1-eastus",
                "location_name": "East US",
                "document_endpoint": "https://DA1-eastus.documents.azure.com:443/",
                "provisioning_state": "Succeeded",
                "failover_priority": 0,
            },
            {
                "id": "DA1-centralindia",
                "location_name": "Central India",
                "document_endpoint": "https://DA1-centralindia.documents.azure.com:443/",
                "provisioning_state": "Succeeded",
                "failover_priority": 0,
            },
        ],
        "locations": [
            {
                "id": "DA1-eastus",
                "location_name": "East US",
                "document_endpoint": "https://DA1-eastus.documents.azure.com:443/",
                "provisioning_state": "Succeeded",
                "failover_priority": 0,
            },
            {
                "id": "DA1-centralindia",
                "location_name": "Central India",
                "document_endpoint": "https://DA1-centralindia.documents.azure.com:443/",
                "provisioning_state": "Succeeded",
                "failover_priority": 0,
            },
            {
                "id": "DA1-japaneast",
                "location_name": "Japan East",
                "document_endpoint": "https://DA1-japaneast.documents.azure.com:443/",
                "provisioning_state": "Succeeded",
                "failover_priority": 0,
            },
        ],
        "failover_policies": [
            {
                "id": "DA1-eastus",
                "location_name": "East US",
                "failover_priority": 0,
            },
        ],
        "private_endpoint_connections": [
            {
                "id": da1 + "/privateEndpointConnections/pe1",
                "private_endpoint": {
                    "id": rg + "/providers/Microsoft.Network/privateEndpoints/pe1",
                },
                "private_link_service_connection_state": {
                    "status": "Approved",
                    "actions_required": "None",
                },
            },
        ],
        "cors": [
            {
                "cors_policy_unique_id": cors1_id,
                "allowed_origins": "*",
            },
        ],
        "virtual_network_rules": [
            {
                "id": rg + "/providers/Microsoft.Network/virtualNetworks/vn1",
                "ignore_missing_v_net_service_endpoint": False,
            },
        ],
    },
    {
        "id": da2,
        "name": "DA2",
        "resourceGroup": "RG",
        "location": "West US",
        "type": "Microsoft.DocumentDB/databaseAccounts",
        "kind": "GlobalDocumentDB",
        "tags": {"env": "prod", "dept": "finance"},
        "provisioning_state": "Succeeded",
        "document_endpoint": "https://ddb1.documents.azure.com:444/",
        "is_virtual_network_filter_enabled": True,
        "enable_automatic_failover": True,
        "enable_multiple_write_locations": True,
        "database_account_offer_type": "Standard",
        "disable_key_based_metadata_write_access": False,
        "enable_free_tier": False,
        "enable_analytical_storage": True,
        "consistency_policy": {
            "default_consistency_level": "Session",
            "max_interval_in_seconds": 5,
            "max_staleness_prefix": 100,
        },
        "failover_policies": [
            {
                "id": "DA2-eastus",
                "location_name": "East US",
                "failover_priority": 0,
            },
        ],
        "private_endpoint_connections": [
            {
                "id": da2 + "/privateEndpointConnections/pe2",
                "private_endpoint": {
                    "id": rg + "/providers/Microsoft.Network/privateEndpoints/pe2",
                },
                "private_link_service_connection_state": {
                    "status": "Approved",
                    "actions_required": "None",
                },
            },
        ],
        "cors": [
            {
                "cors_policy_unique_id": cors2_id,
                "allowed_origins": "*",
            },
        ],
        "virtual_network_rules": [
            {
                "id": rg + "/providers/Microsoft.Network/virtualNetworks/vn2",
                "ignore_missing_v_net_service_endpoint": False,
            },
        ],
    },
]

DESCRIBE_SQL_DATABASES = [
    {
        "id": da1 + "/sqlDatabases/sql_db1",
        "name": "sql_db1",
        "type": "Microsoft.DocumentDB/databaseAccounts/sqlDatabases",
        "location": "West US",
        "tags": {},
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "database_account_id": da1,
    },
    {
        "id": da2 + "/sqlDatabases/sql_db2",
        "name": "sql_db2",
        "type": "Microsoft.DocumentDB/databaseAccounts/sqlDatabases",
        "location": "West US",
        "tags": {},
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "database_account_id": da2,
    },
]

DESCRIBE_CASSANDRA_KEYSPACES = [
    {
        "id": da1 + "/cassandraKeyspaces/cass_ks1",
        "name": "cass_ks1",
        "type": "Microsoft.DocumentDB/databaseAccounts/cassandraKeyspaces",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "database_account_id": da1,
    },
    {
        "id": da2 + "/cassandraKeyspaces/cass_ks2",
        "name": "cass_ks2",
        "type": "Microsoft.DocumentDB/databaseAccounts/cassandraKeyspaces",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "database_account_id": da2,
    },
]

DESCRIBE_MONGODB_DATABASES = [
    {
        "id": da1 + "/mongodbDatabases/mongo_db1",
        "name": "mongo_db1",
        "type": "Microsoft.DocumentDB/databaseAccounts/mongodbDatabases",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "database_account_id": da1,
    },
    {
        "id": da2 + "/mongodbDatabases/mongo_db2",
        "name": "mongo_db2",
        "type": "Microsoft.DocumentDB/databaseAccounts/mongodbDatabases",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "database_account_id": da2,
    },
]

DESCRIBE_TABLE_RESOURCES = [
    {
        "id": da1 + "/tables/table1",
        "name": "table1",
        "type": "Microsoft.DocumentDB/databaseAccounts/tables",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "database_account_id": da1,
    },
    {
        "id": da2 + "/tables/table2",
        "name": "table2",
        "type": "Microsoft.DocumentDB/databaseAccounts/tables",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "database_account_id": da2,
    },
]

DESCRIBE_SQL_CONTAINERS = [
    {
        "id": da1 + "/sqlDatabases/sql_db1/sqlContainers/con1",
        "name": "con1",
        "type": "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/sqlContainers",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "resource": {
            "id": "test-con1",
            "indexing_policy": {
                "indexing_mode": "Consistent",
                "automatic": True,
            },
            "default_ttl": 100,
            "conflict_resolution_policy": {
                "mode": "LastWriterWins",
            },
        },
        "database_id": da1 + "/sqlDatabases/sql_db1",
    },
    {
        "id": da2 + "/sqlDatabases/sql_db2/sqlContainers/con2",
        "name": "con2",
        "type": "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/sqlContainers",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "resource": {
            "id": "test-con2",
            "indexing_policy": {
                "indexing_mode": "Consistent",
                "automatic": True,
            },
            "default_ttl": 100,
            "conflict_resolution_policy": {
                "mode": "LastWriterWins",
            },
        },
        "database_id": da2 + "/sqlDatabases/sql_db2",
    },
]

DESCRIBE_CASSANDRA_TABLES = [
    {
        "id": da1 + "/cassandraKeyspaces/cass_ks1/cassandraTables/table1",
        "name": "table1",
        "type": "Microsoft.DocumentDB/databaseAccounts/cassandraKeyspaces/cassandraTables",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "resource": {
            "id": "table1",
            "default_ttl": 100,
            "analytical_storage_ttl": 500,
        },
        "keyspace_id": da1 + "/cassandraKeyspaces/cass_ks1",
    },
    {
        "id": da2 + "/cassandraKeyspaces/cass_ks2/cassandraTables/table2",
        "name": "table2",
        "type": "Microsoft.DocumentDB/databaseAccounts/cassandraKeyspaces/cassandraTables",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "resource": {
            "id": "table2",
            "default_ttl": 100,
            "analytical_storage_ttl": 500,
        },
        "keyspace_id": da2 + "/cassandraKeyspaces/cass_ks2",
    },
]

DESCRIBE_MONGODB_COLLECTIONS = [
    {
        "id": da1 + "/mongodbDatabases/mongo_db1/mongodbCollections/col1",
        "name": "col1",
        "type": "Microsoft.DocumentDB/databaseAccounts/mongodbDatabases/mongodbCollections",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "resource": {
            "id": "testcoll",
            "analytical_storage_ttl": 500,
        },
        "database_id": da1 + "/mongodbDatabases/mongo_db1",
    },
    {
        "id": da2 + "/mongodbDatabases/mongo_db2/mongodbCollections/col2",
        "name": "col2",
        "type": "Microsoft.DocumentDB/databaseAccounts/mongodbDatabases/mongodbCollections",
        "location": "West US",
        "options": {
            "throughput": 100,
            "autoscale_settings": {
                "max_throughput": 1000,
            },
        },
        "resource": {
            "id": "testcoll",
            "analytical_storage_ttl": 500,
        },
        "database_id": da2 + "/mongodbDatabases/mongo_db2",
    },
]
