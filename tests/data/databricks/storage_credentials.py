from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

DATABRICKS_STORAGE_CRED_AWS_ARN = "arn:aws:iam::123456789012:role/uc-storage-role"
DATABRICKS_STORAGE_CRED_GCP_EMAIL = "uc-storage@my-project.iam.gserviceaccount.com"

DATABRICKS_STORAGE_CREDENTIALS = [
    {
        "id": "283aa653-9513-4548-b877-99b0bef94797",
        "name": "aws-uc-storage-cred",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "owner": "kunaal@subimage.io",
        "read_only": False,
        "used_for_managed_storage": True,
        "isolation_mode": "ISOLATION_MODE_OPEN",
        "created_at": 1782835898723,
        "updated_at": 1782835898723,
        "aws_iam_role": {
            "role_arn": DATABRICKS_STORAGE_CRED_AWS_ARN,
            "external_id": "abc123",
            "unity_catalog_iam_arn": "arn:aws:iam::414351767826:role/unity-catalog",
        },
    },
    {
        "id": "393bb764-0624-5659-c988-00c1cfa05808",
        "name": "gcp-uc-storage-cred",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "owner": "kunaal@subimage.io",
        "read_only": True,
        "used_for_managed_storage": False,
        "isolation_mode": "ISOLATION_MODE_OPEN",
        "created_at": 1782835898999,
        "updated_at": 1782835898999,
        "databricks_gcp_service_account": {
            "email": DATABRICKS_STORAGE_CRED_GCP_EMAIL,
            "credential_id": "cred-999",
        },
    },
]
