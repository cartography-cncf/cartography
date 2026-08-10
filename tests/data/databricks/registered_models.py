from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

DATABRICKS_REGISTERED_MODELS = [
    {
        "name": "churn_model",
        "full_name": "prod.finance.churn_model",
        "catalog_name": "prod",
        "schema_name": "finance",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "id": "model-1111",
        "owner": "ml-eng@subimage.io",
        "storage_location": "s3://prod-models/churn",
        "created_at": 1782835899600,
        "updated_at": 1782835899600,
        "created_by": "ml-eng@subimage.io",
        "updated_by": "ml-eng@subimage.io",
    },
]

DATABRICKS_MODEL_VERSIONS = [
    {
        "version": 1,
        "model_name": "churn_model",
        "catalog_name": "prod",
        "schema_name": "finance",
        "metastore_id": DATABRICKS_METASTORE_ID,
        "id": "mv-1111",
        "status": "READY",
        "source": "dbfs:/databricks/mlflow/1",
        "run_id": "run-abcdef",
        "created_at": 1782835899700,
        "updated_at": 1782835899700,
        "created_by": "ml-eng@subimage.io",
        "updated_by": "ml-eng@subimage.io",
    },
]
