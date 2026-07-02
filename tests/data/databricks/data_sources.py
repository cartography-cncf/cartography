from tests.data.databricks.sql_warehouses import DATABRICKS_WAREHOUSE_ID

# Shape returned by data_sources.get() (a bare list).
DATABRICKS_DATA_SOURCES = [
    {
        "id": "1811cbc7-42e8-46f9-875c-b613109cd172",
        "name": "Serverless Starter Warehouse",
        "type": "databricks_internal",
        "warehouse_id": DATABRICKS_WAREHOUSE_ID,
        "syntax": "sql",
        "paused": 0,
        "view_only": False,
    },
]
