from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

DATABRICKS_FUNCTIONS = [
    {
        "name": "mask_ssn",
        "full_name": "prod.finance.mask_ssn",
        "catalog_name": "prod",
        "schema_name": "finance",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "function_id": "func-1111",
        "data_type": "STRING",
        "routine_body": "SQL",
        "security_type": "DEFINER",
        "sql_data_access": "READS_SQL_DATA",
        "is_deterministic": True,
        "owner": "data-eng@subimage.io",
        "created_at": 1782835899500,
        "updated_at": 1782835899500,
        "created_by": "data-eng@subimage.io",
        "updated_by": "data-eng@subimage.io",
    },
]
