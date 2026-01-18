DESCRIBE_STORAGE_ACCOUNTS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/testSG1",
        "kind": "Storage",
        "location": "Central India",
        "name": "testSG1",
        "is_hns_enabled": True,
        "creation_time": "2017-05-24T13:24:47.818801Z",
        "primary_location": "Central India",
        "provisioning_state": "Succeeded",
        "secondary_location": "West US 2",
        "status_of_primary": "available",
        "status_of_secondary": "available",
        "enable_https_traffic_only": False,
        "type": "Microsoft.Storage/storageAccounts",
        "tags": {"env": "prod", "dept": "finance"},
        "resourceGroup": "TestRG",
    },
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/testSG2",
        "kind": "Storage",
        "location": "Central India",
        "name": "testSG2",
        "is_hns_enabled": True,
        "creation_time": "2017-05-24T13:24:47.818801Z",
        "primary_location": "Central India",
        "provisioning_state": "Succeeded",
        "secondary_location": "West US 2",
        "status_of_primary": "available",
        "status_of_secondary": "available",
        "enable_https_traffic_only": False,
        "type": "Microsoft.Storage/storageAccounts",
        "tags": {"env": "prod", "dept": "engineering"},
        "resourceGroup": "TestRG",
    },
]

sa1 = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/testSG1"
sa2 = "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/testSG2"


DESCRIBE_QUEUE_SERVICES = [
    {
        "id": sa1 + "/queueServices/QS1",
        "name": "QS1",
        "type": "Microsoft.Storage/storageAccounts/queueServices",
        "storage_account_id": sa1,
    },
    {
        "id": sa2 + "/queueServices/QS2",
        "name": "QS2",
        "type": "Microsoft.Storage/storageAccounts/queueServices",
        "storage_account_id": sa2,
    },
]


DESCRIBE_TABLE_SERVICES = [
    {
        "id": sa1 + "/tableServices/TS1",
        "name": "TS1",
        "type": "Microsoft.Storage/storageAccounts/tableServices",
        "storage_account_id": sa1,
    },
    {
        "id": sa2 + "/tableServices/TS2",
        "name": "TS2",
        "type": "Microsoft.Storage/storageAccounts/tableServices",
        "storage_account_id": sa2,
    },
]


DESCRIBE_FILE_SERVICES = [
    {
        "id": sa1 + "/fileServices/FS1",
        "name": "FS1",
        "type": "Microsoft.Storage/storageAccounts/fileServices",
        "storage_account_id": sa1,
    },
    {
        "id": sa2 + "/fileServices/FS2",
        "name": "FS2",
        "type": "Microsoft.Storage/storageAccounts/fileServices",
        "storage_account_id": sa2,
    },
]


DESCRIBE_BLOB_SERVICES = [
    {
        "id": sa1 + "/blobServices/BS1",
        "name": "BS1",
        "type": "Microsoft.Storage/storageAccounts/blobServices",
        "storage_account_id": sa1,
    },
    {
        "id": sa2 + "/blobServices/BS2",
        "name": "BS2",
        "type": "Microsoft.Storage/storageAccounts/blobServices",
        "storage_account_id": sa2,
    },
]


DESCRIBE_QUEUE = [
    {
        "id": sa1 + "/queueServices/QS1/queues/queue1",
        "name": "queue1",
        "type": "Microsoft.Storage/storageAccounts/queueServices/queues",
        "service_id": sa1 + "/queueServices/QS1",
    },
    {
        "id": sa2 + "/queueServices/QS2/queues/queue2",
        "name": "queue2",
        "type": "Microsoft.Storage/storageAccounts/queueServices/queues",
        "service_id": sa2 + "/queueServices/QS2",
    },
]


DESCRIBE_TABLES = [
    {
        "id": sa1 + "/tableServices/TS1/tables/table1",
        "name": "table1",
        "type": "Microsoft.Storage/storageAccounts/tableServices/tables",
        "service_id": sa1 + "/tableServices/TS1",
    },
    {
        "id": sa2 + "/tableServices/TS2/tables/table2",
        "name": "table2",
        "type": "Microsoft.Storage/storageAccounts/tableServices/tables",
        "service_id": sa2 + "/tableServices/TS2",
    },
]


DESCRIBE_FILE_SHARES = [
    {
        "id": sa1 + "/fileServices/FS1/shares/share1",
        "name": "share1",
        "type": "Microsoft.Storage/storageAccounts/fileServices/shares",
        "etag": '"0x8D589847D51C7DE"',
        "last_modified_time": "2019-05-14T08:20:47Z",
        "share_quota": 1024,
        "version": "1234567890",
        "deleted": True,
        "deleted_time": "2019-12-14T08:20:47Z",
        "remaining_retention_days": 30,
        "service_id": sa1 + "/fileServices/FS1",
    },
    {
        "id": sa2 + "/fileServices/FS2/shares/share2",
        "name": "share2",
        "type": "Microsoft.Storage/storageAccounts/fileServices/shares",
        "etag": '"0x8D589847D51C7DE"',
        "last_modified_time": "2019-05-14T08:20:47Z",
        "share_quota": 1024,
        "version": "1234567890",
        "remaining_retention_days": 30,
        "service_id": sa2 + "/fileServices/FS2",
    },
]


DESCRIBE_BLOB_CONTAINERS = [
    {
        "id": sa1 + "/blobServices/BS1/containers/container1",
        "name": "container1",
        "type": "Microsoft.Storage/storageAccounts/blobServices/containers",
        "etag": '"0x8D589847D51C7DE"',
        "public_access": "Container",
        "lease_status": "Unlocked",
        "lease_state": "Available",
        "last_modified_time": "2018-03-14T08:20:47Z",
        "has_immutability_policy": False,
        "has_legal_hold": False,
        "service_id": sa1 + "/blobServices/BS1",
    },
    {
        "id": sa2 + "/blobServices/BS2/containers/container2",
        "name": "container2",
        "type": "Microsoft.Storage/storageAccounts/blobServices/containers",
        "etag": '"0x8D589847D51C7DE"',
        "public_access": "Container",
        "lease_status": "Unlocked",
        "lease_state": "Available",
        "last_modified_time": "2018-03-14T08:20:47Z",
        "has_immutability_policy": False,
        "has_legal_hold": False,
        "service_id": sa2 + "/blobServices/BS2",
    },
]
