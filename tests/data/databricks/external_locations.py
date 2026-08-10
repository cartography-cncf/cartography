from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

DATABRICKS_EXTERNAL_LOCATION_S3_BUCKET = "dbstorage-prod-ubjuy"

DATABRICKS_EXTERNAL_LOCATIONS = [
    {
        "id": "483378ee-ee5f-46d6-92ac-106b5a524184",
        "name": "managed_storage_location",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "url": f"s3://{DATABRICKS_EXTERNAL_LOCATION_S3_BUCKET}/uc/data",
        "credential_id": "283aa653-9513-4548-b877-99b0bef94797",
        "credential_name": "aws-uc-storage-cred",
        "read_only": False,
        "isolation_mode": "ISOLATION_MODE_OPEN",
        "fallback": False,
        "owner": "System user",
        "created_at": 1782835898723,
        "updated_at": 1782835898723,
    },
]
