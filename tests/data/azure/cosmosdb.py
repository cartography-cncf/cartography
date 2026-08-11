# These payloads mirror `as_dict()` on azure-mgmt-cosmosdb 10.0.0 hybrid models: resource
# fields live under `properties` with ARM camelCase names. The `resourceGroup`,
# `database_account_id`, `database_id` and `keyspace_id` keys are the exceptions; those are
# injected by cartography (or, here, by the mocked getters) rather than returned by the SDK.
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
        "properties": {
            "provisioningState": "Succeeded",
            "documentEndpoint": "https://ddb1.documents.azure.com:443/",
            "databaseAccountOfferType": "Standard",
            "isVirtualNetworkFilterEnabled": True,
            "enableAutomaticFailover": True,
            "enableMultipleWriteLocations": True,
            "disableKeyBasedMetadataWriteAccess": False,
            "enableFreeTier": False,
            "enableAnalyticalStorage": True,
            "enableCassandraConnector": False,
            "connectorOffer": "Small",
            "publicNetworkAccess": "Enabled",
            "keyVaultKeyUri": "https://kv1.vault.azure.net/keys/cmk",
            "capabilities": [{"name": "EnableMongo"}],
            "ipRules": [{"ipAddressOrRange": "10.0.0.0/24"}],
            "consistencyPolicy": {
                "defaultConsistencyLevel": "Session",
                "maxIntervalInSeconds": 5,
                "maxStalenessPrefix": 100,
            },
            "writeLocations": [
                {
                    "id": "DA1-eastus",
                    "locationName": "East US",
                    "documentEndpoint": "https://DA1-eastus.documents.azure.com:443/",
                    "provisioningState": "Succeeded",
                    "failoverPriority": 0,
                    "isZoneRedundant": False,
                },
                {
                    "id": "DA1-centralindia",
                    "locationName": "Central India",
                    "documentEndpoint": "https://DA1-centralindia.documents.azure.com:443/",
                    "provisioningState": "Succeeded",
                    "failoverPriority": 0,
                    "isZoneRedundant": False,
                },
            ],
            "readLocations": [
                {
                    "id": "DA1-eastus",
                    "locationName": "East US",
                    "documentEndpoint": "https://DA1-eastus.documents.azure.com:443/",
                    "provisioningState": "Succeeded",
                    "failoverPriority": 0,
                },
                {
                    "id": "DA1-centralindia",
                    "locationName": "Central India",
                    "documentEndpoint": "https://DA1-centralindia.documents.azure.com:443/",
                    "provisioningState": "Succeeded",
                    "failoverPriority": 0,
                },
            ],
            "locations": [
                {
                    "id": "DA1-eastus",
                    "locationName": "East US",
                    "documentEndpoint": "https://DA1-eastus.documents.azure.com:443/",
                    "provisioningState": "Succeeded",
                    "failoverPriority": 0,
                },
                {
                    "id": "DA1-centralindia",
                    "locationName": "Central India",
                    "documentEndpoint": "https://DA1-centralindia.documents.azure.com:443/",
                    "provisioningState": "Succeeded",
                    "failoverPriority": 0,
                },
                {
                    "id": "DA1-japaneast",
                    "locationName": "Japan East",
                    "documentEndpoint": "https://DA1-japaneast.documents.azure.com:443/",
                    "provisioningState": "Succeeded",
                    "failoverPriority": 0,
                },
            ],
            "failoverPolicies": [
                {
                    "id": "DA1-eastus",
                    "locationName": "East US",
                    "failoverPriority": 0,
                },
            ],
            "privateEndpointConnections": [
                {
                    "id": da1 + "/privateEndpointConnections/pe1",
                    "name": "pe1",
                    "properties": {
                        "privateEndpoint": {
                            "id": rg
                            + "/providers/Microsoft.Network/privateEndpoints/pe1",
                        },
                        "privateLinkServiceConnectionState": {
                            "status": "Approved",
                            "actionsRequired": "None",
                        },
                    },
                },
            ],
            "cors": [
                {
                    "allowedOrigins": "*",
                    "allowedMethods": "GET,POST",
                    "allowedHeaders": "x-ms-version",
                    "exposedHeaders": "x-ms-request-charge",
                    "maxAgeInSeconds": 3600,
                },
            ],
            "virtualNetworkRules": [
                {
                    "id": rg + "/providers/Microsoft.Network/virtualNetworks/vn1",
                    "ignoreMissingVNetServiceEndpoint": False,
                },
            ],
        },
    },
    {
        "id": da2,
        "name": "DA2",
        "resourceGroup": "RG",
        "location": "West US",
        "type": "Microsoft.DocumentDB/databaseAccounts",
        "kind": "GlobalDocumentDB",
        "tags": {"env": "prod", "dept": "finance"},
        "properties": {
            "provisioningState": "Succeeded",
            "documentEndpoint": "https://ddb1.documents.azure.com:444/",
            "databaseAccountOfferType": "Standard",
            "isVirtualNetworkFilterEnabled": True,
            "enableAutomaticFailover": True,
            "enableMultipleWriteLocations": True,
            "disableKeyBasedMetadataWriteAccess": False,
            "enableFreeTier": False,
            "enableAnalyticalStorage": True,
            "consistencyPolicy": {
                "defaultConsistencyLevel": "Session",
                "maxIntervalInSeconds": 5,
                "maxStalenessPrefix": 100,
            },
            "failoverPolicies": [
                {
                    "id": "DA2-eastus",
                    "locationName": "East US",
                    "failoverPriority": 0,
                },
            ],
            "privateEndpointConnections": [
                {
                    "id": da2 + "/privateEndpointConnections/pe2",
                    "name": "pe2",
                    "properties": {
                        "privateEndpoint": {
                            "id": rg
                            + "/providers/Microsoft.Network/privateEndpoints/pe2",
                        },
                        "privateLinkServiceConnectionState": {
                            "status": "Approved",
                            "actionsRequired": "None",
                        },
                    },
                },
            ],
            "cors": [
                {
                    "allowedOrigins": "*",
                    "allowedMethods": "GET",
                    "allowedHeaders": "x-ms-version",
                    "exposedHeaders": "x-ms-request-charge",
                    "maxAgeInSeconds": 600,
                },
            ],
            "virtualNetworkRules": [
                {
                    "id": rg + "/providers/Microsoft.Network/virtualNetworks/vn2",
                    "ignoreMissingVNetServiceEndpoint": False,
                },
            ],
        },
    },
]


def _throughput_options() -> dict:
    """
    Fresh copy per fixture: the transforms normalize these dicts in place.
    """
    return {
        "throughput": 100,
        "autoscaleSettings": {
            "maxThroughput": 1000,
        },
    }


DESCRIBE_SQL_DATABASES = [
    {
        "id": da1 + "/sqlDatabases/sql_db1",
        "name": "sql_db1",
        "type": "Microsoft.DocumentDB/databaseAccounts/sqlDatabases",
        "location": "West US",
        "tags": {},
        "properties": {
            "resource": {"id": "sql_db1"},
            "options": _throughput_options(),
        },
        "database_account_id": da1,
    },
    {
        "id": da2 + "/sqlDatabases/sql_db2",
        "name": "sql_db2",
        "type": "Microsoft.DocumentDB/databaseAccounts/sqlDatabases",
        "location": "West US",
        "tags": {},
        "properties": {
            "resource": {"id": "sql_db2"},
            "options": _throughput_options(),
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
        "properties": {
            "resource": {"id": "cass_ks1"},
            "options": _throughput_options(),
        },
        "database_account_id": da1,
    },
    {
        "id": da2 + "/cassandraKeyspaces/cass_ks2",
        "name": "cass_ks2",
        "type": "Microsoft.DocumentDB/databaseAccounts/cassandraKeyspaces",
        "location": "West US",
        "properties": {
            "resource": {"id": "cass_ks2"},
            "options": _throughput_options(),
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
        "properties": {
            "resource": {"id": "mongo_db1"},
            "options": _throughput_options(),
        },
        "database_account_id": da1,
    },
    {
        "id": da2 + "/mongodbDatabases/mongo_db2",
        "name": "mongo_db2",
        "type": "Microsoft.DocumentDB/databaseAccounts/mongodbDatabases",
        "location": "West US",
        "properties": {
            "resource": {"id": "mongo_db2"},
            "options": _throughput_options(),
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
        "properties": {
            "resource": {"id": "table1"},
            "options": _throughput_options(),
        },
        "database_account_id": da1,
    },
    {
        "id": da2 + "/tables/table2",
        "name": "table2",
        "type": "Microsoft.DocumentDB/databaseAccounts/tables",
        "location": "West US",
        "properties": {
            "resource": {"id": "table2"},
            "options": _throughput_options(),
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
        "properties": {
            "resource": {
                "id": "test-con1",
                "defaultTtl": 100,
                "analyticalStorageTtl": 500,
                "indexingPolicy": {
                    "indexingMode": "Consistent",
                    "automatic": True,
                },
                "conflictResolutionPolicy": {
                    "mode": "LastWriterWins",
                },
            },
            "options": _throughput_options(),
        },
        "database_id": da1 + "/sqlDatabases/sql_db1",
    },
    {
        "id": da2 + "/sqlDatabases/sql_db2/sqlContainers/con2",
        "name": "con2",
        "type": "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/sqlContainers",
        "location": "West US",
        "properties": {
            "resource": {
                "id": "test-con2",
                "defaultTtl": 100,
                "analyticalStorageTtl": 500,
                "indexingPolicy": {
                    "indexingMode": "Consistent",
                    "automatic": True,
                },
                "conflictResolutionPolicy": {
                    "mode": "LastWriterWins",
                },
            },
            "options": _throughput_options(),
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
        "properties": {
            "resource": {
                "id": "table1",
                "defaultTtl": 100,
                "analyticalStorageTtl": 500,
            },
            "options": _throughput_options(),
        },
        "keyspace_id": da1 + "/cassandraKeyspaces/cass_ks1",
    },
    {
        "id": da2 + "/cassandraKeyspaces/cass_ks2/cassandraTables/table2",
        "name": "table2",
        "type": "Microsoft.DocumentDB/databaseAccounts/cassandraKeyspaces/cassandraTables",
        "location": "West US",
        "properties": {
            "resource": {
                "id": "table2",
                "defaultTtl": 100,
                "analyticalStorageTtl": 500,
            },
            "options": _throughput_options(),
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
        "properties": {
            "resource": {
                "id": "testcoll",
                "analyticalStorageTtl": 500,
            },
            "options": _throughput_options(),
        },
        "database_id": da1 + "/mongodbDatabases/mongo_db1",
    },
    {
        "id": da2 + "/mongodbDatabases/mongo_db2/mongodbCollections/col2",
        "name": "col2",
        "type": "Microsoft.DocumentDB/databaseAccounts/mongodbDatabases/mongodbCollections",
        "location": "West US",
        "properties": {
            "resource": {
                "id": "testcoll",
                "analyticalStorageTtl": 500,
            },
            "options": _throughput_options(),
        },
        "database_id": da2 + "/mongodbDatabases/mongo_db2",
    },
]
