DATABRICKS_CRED_CONFIG_AWS_ARN = (
    "arn:aws:iam::123456789012:role/databricks-cross-account-role"
)
DATABRICKS_CRED_CONFIG_AWS_ACCOUNT_ID = "123456789012"

DATABRICKS_CREDENTIAL_CONFIGS = [
    {
        "credentials_id": "cred-abc-123",
        "credentials_name": "prod-cross-account",
        "account_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
        "aws_credentials": {
            "sts_role": {
                "role_arn": DATABRICKS_CRED_CONFIG_AWS_ARN,
                "external_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
            },
        },
        "creation_time": 1782835898723,
    },
    {
        "credentials_id": "cred-def-456",
        "credentials_name": "dev-cross-account",
        "account_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
        "aws_credentials": {
            "sts_role": {
                "role_arn": "arn:aws:iam::999988887777:role/dev-role",
            },
        },
        "creation_time": 1782835899999,
    },
]
