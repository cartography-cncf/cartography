from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

# Shape returned by online_tables.get() (online-tables API response + the
# injected _metastore_id from the source table graph lookup).
DATABRICKS_ONLINE_TABLES = [
    {
        "name": "prod.finance.customers_online",
        "_metastore_id": DATABRICKS_METASTORE_ID,
        "spec": {
            "source_table_full_name": "prod.finance.customers",
            "primary_key_columns": ["id"],
            "timeseries_key": "updated_at",
            "pipeline_id": "pipe-1111",
        },
        "status": {"detailed_state": "ONLINE_NO_PENDING_UPDATE"},
        "unity_catalog_provisioning_state": "ACTIVE",
        "table_serving_url": "https://example.cloud.databricks.com/serving/ot",
    },
]
