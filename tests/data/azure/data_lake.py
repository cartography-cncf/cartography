# Mock response for the `storage_accounts.list()` call
MOCK_STORAGE_ACCOUNTS = [
    {
        # This is a Data Lake enabled account.
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/datalakeaccount",
        "name": "datalakeaccount",
        "properties": {
            "is_hns_enabled": True,
        },
    },
    {
        # This is a standard storage account.
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/standardaccount",
        "name": "standardaccount",
        "properties": {
            "is_hns_enabled": False,
        },
    },
]

# Mock response for the `blob_containers.list()` call
MOCK_FILESYSTEMS = [
    {
        "id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/datalakeaccount/blobServices/default/containers/filesystem1",
        "name": "filesystem1",
        "storage_account_id": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/datalakeaccount",
        "properties": {
            "public_access": "None",
            "last_modified_time": "2025-01-01T12:00:00Z",
            "has_immutability_policy": False,
            "has_legal_hold": True,
        },
    },
]
