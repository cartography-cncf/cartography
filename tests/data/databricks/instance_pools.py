DATABRICKS_INSTANCE_POOLS = [
    {
        "instance_pool_id": "0101-pool-aaaa",
        "instance_pool_name": "shared-warm-pool",
        "node_type_id": "i3.xlarge",
        "min_idle_instances": 0,
        "max_capacity": 10,
        "idle_instance_autotermination_minutes": 15,
        "enable_elastic_disk": True,
        "state": "ACTIVE",
    },
    {
        "instance_pool_id": "0101-pool-driver",
        "instance_pool_name": "driver-only-pool",
        "node_type_id": "i3.2xlarge",
        "min_idle_instances": 0,
        "max_capacity": 4,
        "idle_instance_autotermination_minutes": 15,
        "enable_elastic_disk": True,
        "state": "ACTIVE",
    },
]
