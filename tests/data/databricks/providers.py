from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID

# Shape returned by providers.get() (the "providers" list).
DATABRICKS_PROVIDERS = [
    {
        "name": "acme_data_provider",
        "authentication_type": "TOKEN",
        "owner": "jeremy@subimage.io",
        "comment": "sub-1580 test provider",
        "data_provider_global_metastore_id": "aws:eu-west-1:acme-metastore",
        "cloud": "aws",
        "region": "eu-west-1",
        "created_at": 1782952000000,
        "created_by": "jeremy@subimage.io",
        "updated_at": 1782952000000,
    },
]

PROVIDER_ID = f"{DATABRICKS_METASTORE_ID}/acme_data_provider"
