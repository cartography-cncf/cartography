from tests.data.databricks.sql_warehouses import DATABRICKS_WAREHOUSE_ID

DATABRICKS_QUERY_ID = "323e781f-df1c-4460-b513-1b293f9d8871"

# Shape returned by queries.get() (the "results" list).
DATABRICKS_QUERIES = [
    {
        "id": DATABRICKS_QUERY_ID,
        "display_name": "carto-test-query",
        "warehouse_id": DATABRICKS_WAREHOUSE_ID,
        "query_text": "SELECT 1 AS carto_test",
        "owner_user_name": "jeremy@subimage.io",
        "last_modifier_user_name": "jeremy@subimage.io",
        "run_as_mode": "OWNER",
        "lifecycle_state": "ACTIVE",
        "parent_path": "/Workspace/Users/jeremy@subimage.io",
        "create_time": "2026-07-01T23:27:40Z",
        "update_time": "2026-07-01T23:27:40Z",
    },
]
