"""
Test data for Azure permission relationships integration tests.
Contains only Azure resource data and YAML configuration.
"""

# Mock Azure Subscription
AZURE_SUBSCRIPTION = {
    "id": "/subscriptions/12345678-1234-1234-1234-123456789012",
    "subscriptionId": "12345678-1234-1234-1234-123456789012",
    "displayName": "Test Subscription",
    "state": "Enabled",
}

# Mock Azure SQL Servers
AZURE_SQL_SERVERS = [
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL1",
        "name": "testSQL1",
        "type": "Microsoft.Sql/servers",
        "location": "East US",
        "kind": "v12.0",
        "version": "12.0",
        "state": "Ready",
        "resourceGroup": "TestRG",
    },
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Sql/servers/testSQL2",
        "name": "testSQL2",
        "type": "Microsoft.Sql/servers",
        "location": "West US",
        "kind": "v12.0",
        "version": "12.0",
        "state": "Ready",
        "resourceGroup": "TestRG",
    },
]

# Mock Azure Storage Accounts
AZURE_STORAGE_ACCOUNTS = [
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/teststorage1",
        "kind": "Storage",
        "location": "East US",
        "name": "teststorage1",
        "is_hns_enabled": True,
        "creation_time": "2017-05-24T13:24:47.818801Z",
        "primary_location": "East US",
        "provisioning_state": "Succeeded",
        "secondary_location": "West US 2",
        "status_of_primary": "available",
        "status_of_secondary": "available",
        "enable_https_traffic_only": False,
        "type": "Microsoft.Storage/storageAccounts",
        "resourceGroup": "TestRG",
    },
]

# Mock Azure Virtual Machines
AZURE_VMS = [
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/testVM1",
        "type": "Microsoft.Compute/virtualMachines",
        "location": "East US",
        "resource_group": "TestRG",
        "name": "testVM1",
        "plan": {
            "product": "Standard",
        },
        "hardware_profile": {
            "vm_size": "Standard_D2s_v3",
        },
        "license_type": "Windows_Client",
        "os_profile": {
            "computer_name": "testVM1",
        },
        "identity": {
            "type": "SystemAssigned",
        },
        "zones": [
            "East US",
        ],
        "additional_capabilities": {
            "ultra_ssd_enabled": True,
        },
        "priority": "Low",
        "eviction_policy": "Deallocate",
    },
]

# Mock Azure CosmosDB Accounts
AZURE_COSMOSDB_ACCOUNTS = [
    {
        "id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/TestRG/providers/Microsoft.DocumentDB/databaseAccounts/testcosmos1",
        "name": "testcosmos1",
        "resourceGroup": "TestRG",
        "location": "East US",
        "type": "Microsoft.DocumentDB/databaseAccounts",
        "kind": "GlobalDocumentDB",
        "tags": {},
        "provisioning_state": "Succeeded",
        "document_endpoint": "https://testcosmos1.documents.azure.com:443/",
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
                "id": "testcosmos1-eastus",
                "location_name": "East US",
                "document_endpoint": "https://testcosmos1-eastus.documents.azure.com:443/",
                "provisioning_state": "Succeeded",
                "failover_priority": 0,
                "is_zone_redundant": False,
            }
        ],
        "read_locations": [
            {
                "id": "testcosmos1-eastus",
                "location_name": "East US",
                "document_endpoint": "https://testcosmos1-eastus.documents.azure.com:443/",
                "provisioning_state": "Succeeded",
                "failover_priority": 0,
                "is_zone_redundant": False,
            }
        ],
        "locations": [
            {
                "id": "testcosmos1-eastus",
                "location_name": "East US",
                "document_endpoint": "https://testcosmos1-eastus.documents.azure.com:443/",
                "provisioning_state": "Succeeded",
                "failover_priority": 0,
                "is_zone_redundant": False,
            }
        ],
        "cors": [
            {
                "allowed_origins": "*",
                "allowed_methods": "GET,PUT,POST,DELETE,HEAD,OPTIONS",
                "allowed_headers": "*",
                "exposed_headers": "*",
                "max_age_in_seconds": 200,
            }
        ],
        "private_endpoint_connections": [],
        "virtual_network_rules": [],
        "ip_rules": [],
    },
]

# Permission Relationships YAML Configuration
PERMISSION_RELATIONSHIPS_YAML = """
- target_label: AzureSQLServer
  permissions:
  - Microsoft.Sql/servers/delete
  - Microsoft.Sql/servers/write
  - Microsoft.Sql/servers/administrators/write
  - Microsoft.Sql/servers/securityAlertPolicies/write
  - Microsoft.Sql/servers/vulnerabilityAssessments/write
  - Microsoft.Sql/servers/auditingSettings/write
  - Microsoft.Sql/servers/encryptionProtector/write
  - Microsoft.Sql/servers/transparentDataEncryption/write
  relationship_name: CAN_MANAGE

- target_label: AzureSQLServer
  permissions:
  - Microsoft.Sql/servers/read
  - Microsoft.Sql/servers/databases/read
  - Microsoft.Sql/servers/administrators/read
  - Microsoft.Sql/servers/securityAlertPolicies/read
  - Microsoft.Sql/servers/vulnerabilityAssessments/read
  - Microsoft.Sql/servers/auditingSettings/read
  - Microsoft.Sql/servers/encryptionProtector/read
  - Microsoft.Sql/servers/transparentDataEncryption/read
  relationship_name: CAN_READ

- target_label: AzureSQLServer
  permissions:
  - Microsoft.Sql/servers/write
  - Microsoft.Sql/servers/databases/write
  - Microsoft.Sql/servers/administrators/write
  - Microsoft.Sql/servers/securityAlertPolicies/write
  - Microsoft.Sql/servers/vulnerabilityAssessments/write
  - Microsoft.Sql/servers/auditingSettings/write
  - Microsoft.Sql/servers/encryptionProtector/write
  - Microsoft.Sql/servers/transparentDataEncryption/write
  relationship_name: CAN_WRITE

- target_label: AzureStorageAccount
  permissions:
  - Microsoft.Storage/storageAccounts/read
  - Microsoft.Storage/storageAccounts/write
  - Microsoft.Storage/storageAccounts/delete
  - Microsoft.Storage/storageAccounts/blobServices/containers/read
  - Microsoft.Storage/storageAccounts/blobServices/containers/write
  - Microsoft.Storage/storageAccounts/blobServices/containers/delete
  relationship_name: CAN_MANAGE

- target_label: AzureStorageAccount
  permissions:
  - Microsoft.Storage/storageAccounts/read
  - Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read
  - Microsoft.Storage/storageAccounts/queueServices/queues/messages/read
  - Microsoft.Storage/storageAccounts/tableServices/tables/entities/read
  relationship_name: CAN_READ

- target_label: AzureVirtualMachine
  permissions:
  - Microsoft.Compute/virtualMachines/read
  - Microsoft.Compute/virtualMachines/write
  - Microsoft.Compute/virtualMachines/delete
  - Microsoft.Compute/virtualMachines/start/action
  - Microsoft.Compute/virtualMachines/restart/action
  - Microsoft.Compute/virtualMachines/powerOff/action
  - Microsoft.Compute/virtualMachines/deallocate/action
  - Microsoft.Compute/virtualMachines/runCommand/action
  relationship_name: CAN_MANAGE

- target_label: AzureVirtualMachine
  permissions:
  - Microsoft.Compute/virtualMachines/read
  - Microsoft.Compute/virtualMachines/instanceView/read
  - Microsoft.Compute/virtualMachines/extensions/read
  relationship_name: CAN_READ

- target_label: AzureCosmosDBAccount
  permissions:
  - Microsoft.DocumentDB/databaseAccounts/read
  - Microsoft.DocumentDB/databaseAccounts/write
  - Microsoft.DocumentDB/databaseAccounts/delete
  - Microsoft.DocumentDB/databaseAccounts/listKeys/action
  - Microsoft.DocumentDB/databaseAccounts/regenerateKey/action
  - Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read
  - Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/write
  - Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/delete
  relationship_name: CAN_MANAGE

- target_label: AzureCosmosDBAccount
  permissions:
  - Microsoft.DocumentDB/databaseAccounts/read
  - Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read
  relationship_name: CAN_READ
"""
