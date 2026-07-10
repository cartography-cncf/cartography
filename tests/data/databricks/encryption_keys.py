DATABRICKS_ENCRYPTION_KEY_AWS_ARN = (
    "arn:aws:kms:us-east-1:123456789012:key/abcd1234-56ef-78ab-90cd-ef1234567890"
)
DATABRICKS_ENCRYPTION_KEY_GCP_NAME = (
    "projects/my-project/locations/us/keyRings/dbx/cryptoKeys/dbx-key"
)

DATABRICKS_ENCRYPTION_KEYS = [
    {
        "customer_managed_key_id": "cmk-abc-123",
        "account_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
        "use_cases": ["MANAGED_SERVICES", "STORAGE"],
        "aws_key_info": {
            "key_arn": DATABRICKS_ENCRYPTION_KEY_AWS_ARN,
            "key_alias": "alias/databricks-cmk",
            "key_region": "us-east-1",
        },
    },
    {
        "customer_managed_key_id": "cmk-def-456",
        "account_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
        "use_cases": ["STORAGE"],
        "gcp_key_info": {"kms_key_id": DATABRICKS_ENCRYPTION_KEY_GCP_NAME},
    },
]
