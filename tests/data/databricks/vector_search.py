DATABRICKS_VECTOR_SEARCH_ENDPOINTS = [
    {
        "name": "vs-endpoint-prod",
        "id": "vse-1111",
        "endpoint_type": "STANDARD",
        "endpoint_status": {"state": "ONLINE"},
        "num_indexes": 1,
        "creator": "ml-eng@subimage.io",
        "creation_timestamp": 1782835899800,
        "last_updated_timestamp": 1782835899800,
    },
]

DATABRICKS_VECTOR_SEARCH_INDEXES = [
    {
        "name": "prod.finance.customers_index",
        "endpoint_name": "vs-endpoint-prod",
        "index_type": "DELTA_SYNC",
        "primary_key": "id",
        "delta_sync_index_spec": {
            "source_table": "prod.finance.customers",
        },
        "creator": "ml-eng@subimage.io",
    },
]
