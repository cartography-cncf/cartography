from tests.data.databricks.sql_warehouses import DATABRICKS_WAREHOUSE_ID

# Shapes as the get_lakeview() / get_legacy() helpers return them: the raw API
# object with a "_type" discriminator added.
DATABRICKS_LAKEVIEW_DASHBOARDS = [
    {
        "_type": "LAKEVIEW",
        "dashboard_id": "01f175a4ac071e099d6cc5ce1c8ba9fb",
        "display_name": "carto-test-dashboard",
        "warehouse_id": DATABRICKS_WAREHOUSE_ID,
        "lifecycle_state": "ACTIVE",
        "parent_path": "/Users/jeremy@subimage.io",
        "path": "/Users/jeremy@subimage.io/carto-test-dashboard.lvdash.json",
        "create_time": "2026-07-01T23:29:14.783Z",
        "update_time": "2026-07-01T23:29:14.869Z",
    },
]

DATABRICKS_LEGACY_DASHBOARDS = [
    {
        "_type": "LEGACY",
        "id": "9a1c2b3d-legacy-4567-89ab-cdef01234567",
        "name": "legacy-sales-dashboard",
        "user": {"email": "kunaal@subimage.io"},
        "created_at": "2025-01-02T10:00:00Z",
        "updated_at": "2025-02-03T11:00:00Z",
        "is_draft": False,
        "is_archived": False,
    },
]
