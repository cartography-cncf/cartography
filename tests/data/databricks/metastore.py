DATABRICKS_METASTORE_ID = "67e22a42-1e24-4a89-80a4-8f78df5ab24f"

# Shape returned by metastores.get(): metastore_summary merged with the
# current-metastore-assignment under the "assignment" key.
DATABRICKS_METASTORE = {
    "cloud": "aws",
    "created_at": 1782835894251,
    "created_by": "System user",
    "delta_sharing_scope": "INTERNAL",
    "external_access_enabled": False,
    "global_metastore_id": f"aws:us-west-2:{DATABRICKS_METASTORE_ID}",
    "metastore_id": DATABRICKS_METASTORE_ID,
    "name": "metastore_aws_us_west_2",
    "owner": "System user",
    "privilege_model_version": "1.0",
    "region": "us-west-2",
    "storage_root": "s3://dbstorage-prod-ubjuy/uc",
    "updated_at": 1782835894251,
    "assignment": {
        "default_catalog_name": "workspace",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "workspace_id": 7474652579390353,
    },
}
