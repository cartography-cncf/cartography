DATABRICKS_WAREHOUSE_ID = "dbd303693ea90e9c"

# Shape returned by sql_warehouses.get() (the "warehouses" list).
DATABRICKS_SQL_WAREHOUSES = [
    {
        "id": DATABRICKS_WAREHOUSE_ID,
        "name": "Serverless Starter Warehouse",
        "state": "STOPPED",
        "cluster_size": "Small",
        "size": "SMALL",
        "warehouse_type": "PRO",
        "enable_serverless_compute": True,
        "enable_photon": True,
        "auto_stop_mins": 10,
        "auto_resume": True,
        "spot_instance_policy": "COST_OPTIMIZED",
        "channel": {"name": "CHANNEL_NAME_CURRENT"},
        "min_num_clusters": 1,
        "max_num_clusters": 1,
        "num_clusters": 0,
        "creator_name": "kunaal@subimage.io",
        "jdbc_url": "jdbc:spark://dbc-aaeaddda-e52f.cloud.databricks.com:443/default",
    },
]
