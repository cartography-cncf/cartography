from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

DATABRICKS_VOLUME_S3_BUCKET = "prod-volume-bucket"

DATABRICKS_VOLUMES = [
    {
        "name": "landing",
        "full_name": "prod.finance.landing",
        "catalog_name": "prod",
        "schema_name": "finance",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "volume_id": "cccc1111-2222-3333-4444-555566667777",
        "volume_type": "EXTERNAL",
        "owner": "data-eng@subimage.io",
        "storage_location": f"s3://{DATABRICKS_VOLUME_S3_BUCKET}/landing",
        "created_at": 1782835899300,
        "updated_at": 1782835899300,
        "created_by": "data-eng@subimage.io",
        "updated_by": "data-eng@subimage.io",
    },
]
