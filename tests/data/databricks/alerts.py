from tests.data.databricks.queries import DATABRICKS_QUERY_ID

# Shape returned by alerts.get() (the "results" list).
DATABRICKS_ALERTS = [
    {
        "id": "b24eb01c-16d1-4235-9caa-428b62f969f2",
        "display_name": "carto-test-alert",
        "query_id": DATABRICKS_QUERY_ID,
        "owner_user_name": "jeremy@subimage.io",
        "state": "UNKNOWN",
        "lifecycle_state": "ACTIVE",
        "condition": {
            "op": "GREATER_THAN",
            "operand": {"column": {"name": "carto_test"}},
            "threshold": {"value": {"double_value": 0}},
        },
        "parent_path": "/Workspace/Users/jeremy@subimage.io",
        "create_time": "2026-07-01T23:28:16Z",
        "update_time": "2026-07-01T23:28:16Z",
    },
]
