DATABRICKS_CLUSTER_POLICIES = [
    {
        "policy_id": "0001-policy-aaaa",
        "name": "Job Compute - Restricted",
        "description": "Job-only clusters, no interactive use.",
        "definition": '{"spark_conf.spark.databricks.cluster.profile": {"type": "fixed", "value": "singleNode"}}',
        "policy_family_id": None,
        "creator_user_name": "jeremy@subimage.io",
        "created_at_timestamp": 1700000050000,
    },
    {
        "policy_id": "0002-policy-bbbb",
        "name": "Personal Compute",
        "description": "Family-derived personal compute.",
        "definition": "{}",
        "policy_family_id": "personal-vm",
        "creator_user_name": None,
        "created_at_timestamp": 1700000060000,
    },
]
