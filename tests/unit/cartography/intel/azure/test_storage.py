from cartography.intel.azure.storage import transform_storage_account
from cartography.intel.azure.storage import transform_storage_blob_container
from cartography.intel.azure.storage import transform_storage_file_share
from cartography.intel.azure.storage import transform_storage_table


def test_transform_storage_account_flattens_sdk_25_properties():
    account = transform_storage_account(
        {
            "id": "account-id",
            "name": "account",
            "properties": {
                "creationTime": "2026-06-01T00:00:00Z",
                "isHnsEnabled": True,
                "primaryLocation": "eastus",
                "provisioningState": "Succeeded",
                "secondaryLocation": "westus",
                "statusOfPrimary": "available",
                "statusOfSecondary": "available",
                "supportsHttpsTrafficOnly": False,
            },
        }
    )

    assert account["creation_time"] == "2026-06-01T00:00:00Z"
    assert account["is_hns_enabled"] is True
    assert account["primary_location"] == "eastus"
    assert account["provisioning_state"] == "Succeeded"
    assert account["secondary_location"] == "westus"
    assert account["status_of_primary"] == "available"
    assert account["status_of_secondary"] == "available"
    assert account["enable_https_traffic_only"] is False


def test_transform_storage_blob_container_flattens_sdk_25_properties():
    container = transform_storage_blob_container(
        {
            "id": "container-id",
            "name": "container",
            "properties": {
                "publicAccess": "Container",
                "leaseStatus": "Unlocked",
                "leaseState": "Available",
                "lastModifiedTime": "2026-06-01T00:00:00Z",
                "hasImmutabilityPolicy": False,
                "hasLegalHold": True,
            },
        }
    )

    assert container["public_access"] == "Container"
    assert container["lease_status"] == "Unlocked"
    assert container["lease_state"] == "Available"
    assert container["last_modified_time"] == "2026-06-01T00:00:00Z"
    assert container["has_immutability_policy"] is False
    assert container["has_legal_hold"] is True


def test_transform_storage_file_share_flattens_sdk_25_properties():
    share = transform_storage_file_share(
        {
            "id": "share-id",
            "name": "share",
            "properties": {
                "lastModifiedTime": "2026-06-01T00:00:00Z",
                "shareQuota": 1024,
                "accessTier": "Hot",
                "remainingRetentionDays": 7,
                "shareUsageBytes": 4096,
                "version": "1",
            },
        }
    )

    assert share["last_modified_time"] == "2026-06-01T00:00:00Z"
    assert share["share_quota"] == 1024
    assert share["access_tier"] == "Hot"
    assert share["remaining_retention_days"] == 7
    assert share["share_usage_bytes"] == 4096
    assert share["version"] == "1"


def test_transform_storage_table_flattens_sdk_25_properties():
    table = transform_storage_table(
        {
            "id": "table-id",
            "name": "table",
            "properties": {
                "tableName": "table1",
            },
        }
    )

    assert table["table_name"] == "table1"
