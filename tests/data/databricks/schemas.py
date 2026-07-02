from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

DATABRICKS_SCHEMAS = [
    {
        "name": "default",
        "full_name": "workspace.default",
        "catalog_name": "workspace",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "schema_id": "5d4d75ee-b421-4ca7-be45-7aa4acb7afb9",
        "owner": "_workspace_admins",
        "comment": "Default schema (auto-created)",
        "created_at": 1782835898859,
        "updated_at": 1782835898859,
        "created_by": "kunaal@subimage.io",
        "updated_by": "kunaal@subimage.io",
    },
    {
        "name": "finance",
        "full_name": "prod.finance",
        "catalog_name": "prod",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "schema_id": "6e5e86ff-c532-5db8-cf56-8bb5bdc8bfc0",
        "owner": "data-eng@subimage.io",
        "created_at": 1782835899000,
        "updated_at": 1782835899000,
        "created_by": "data-eng@subimage.io",
        "updated_by": "data-eng@subimage.io",
    },
]
