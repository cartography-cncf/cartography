DATABRICKS_LOG_DELIVERY_BUCKET = "databricks-audit-logs"

DATABRICKS_LOG_DELIVERY_CONFIGS = [
    {
        "config_id": "log-abc-123",
        "config_name": "audit-log-delivery",
        "account_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
        "log_type": "AUDIT_LOGS",
        "output_format": "JSON",
        "status": "ENABLED",
        "credentials_id": "cred-abc-123",
        "storage_configuration_id": "stg-abc-123",
        "delivery_path_prefix": "audit/",
        "storage_configuration": {
            "root_bucket_info": {"bucket_name": DATABRICKS_LOG_DELIVERY_BUCKET},
        },
    },
    {
        "config_id": "log-def-456",
        "config_name": "billable-usage-delivery",
        "account_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
        "log_type": "BILLABLE_USAGE",
        "output_format": "CSV",
        "status": "ENABLED",
        "credentials_id": "cred-abc-123",
        "storage_configuration_id": "stg-def-456",
        "delivery_path_prefix": "usage/",
    },
]
