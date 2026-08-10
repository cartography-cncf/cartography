DATABRICKS_STORAGE_CONFIG_BUCKET = "databricks-root-bucket"

DATABRICKS_STORAGE_CONFIGS = [
    {
        "storage_configuration_id": "stg-abc-123",
        "storage_configuration_name": "prod-root-storage",
        "account_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
        "root_bucket_info": {"bucket_name": DATABRICKS_STORAGE_CONFIG_BUCKET},
        "creation_time": 1782835898723,
    },
    {
        "storage_configuration_id": "stg-def-456",
        "storage_configuration_name": "dev-root-storage",
        "account_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
        "root_bucket_info": {"bucket_name": "some-other-bucket"},
        "creation_time": 1782835899999,
    },
]
