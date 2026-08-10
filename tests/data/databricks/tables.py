from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

DATABRICKS_TABLE_S3_BUCKET = "prod-data-lake"

DATABRICKS_TABLES = [
    {
        "name": "customers",
        "full_name": "prod.finance.customers",
        "catalog_name": "prod",
        "schema_name": "finance",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "table_id": "aaaa1111-2222-3333-4444-555566667777",
        "table_type": "EXTERNAL",
        "data_source_format": "DELTA",
        "owner": "data-eng@subimage.io",
        "storage_location": f"s3://{DATABRICKS_TABLE_S3_BUCKET}/prod/finance/customers",
        "created_at": 1782835899100,
        "updated_at": 1782835899100,
        "created_by": "data-eng@subimage.io",
        "updated_by": "data-eng@subimage.io",
    },
    {
        "name": "revenue_view",
        "full_name": "prod.finance.revenue_view",
        "catalog_name": "prod",
        "schema_name": "finance",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "table_id": "bbbb1111-2222-3333-4444-555566667777",
        "table_type": "VIEW",
        "owner": "data-eng@subimage.io",
        "view_definition": "SELECT * FROM prod.finance.customers",
        "created_at": 1782835899200,
        "updated_at": 1782835899200,
        "created_by": "data-eng@subimage.io",
        "updated_by": "data-eng@subimage.io",
    },
]
