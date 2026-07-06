from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

DATABRICKS_CATALOGS = [
    {
        "id": "64df693a-f5d8-4d94-9058-ee281d44eac6",
        "name": "workspace",
        "full_name": "workspace",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "catalog_type": "MANAGED_CATALOG",
        "owner": "_workspace_admins",
        "isolation_mode": "ISOLATED",
        "storage_root": "s3://dbstorage-prod-ubjuy/uc",
        "created_at": 1782835898845,
        "updated_at": 1782835901380,
        "created_by": "kunaal@subimage.io",
        "updated_by": "kunaal@subimage.io",
    },
    {
        "id": "aa11bb22-f5d8-4d94-9058-ee281d44eac6",
        "name": "prod",
        "full_name": "prod",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "catalog_type": "MANAGED_CATALOG",
        "owner": "data-eng@subimage.io",
        "isolation_mode": "OPEN",
        "created_at": 1782835898845,
        "updated_at": 1782835901380,
        "created_by": "data-eng@subimage.io",
        "updated_by": "data-eng@subimage.io",
    },
]
