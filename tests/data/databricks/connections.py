from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

DATABRICKS_CONNECTIONS = [
    {
        "name": "snowflake_prod",
        "full_name": "snowflake_prod",
        "connection_id": "conn-1111",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "connection_type": "SNOWFLAKE",
        "credential_type": "USERNAME_PASSWORD",
        "owner": "data-eng@subimage.io",
        "read_only": False,
        "options": {"host": "acme.snowflakecomputing.com", "port": "443"},
        "created_at": 1782835899400,
        "updated_at": 1782835899400,
        "created_by": "data-eng@subimage.io",
        "updated_by": "data-eng@subimage.io",
    },
]
