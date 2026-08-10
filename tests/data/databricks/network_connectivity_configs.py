DATABRICKS_NETWORK_CONNECTIVITY_CONFIGS = [
    {
        "network_connectivity_config_id": "ncc-abc-123",
        "name": "prod-serverless-egress",
        "account_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
        "region": "us-east-1",
        "egress_config": {
            "default_rules": {
                "aws_stable_ip_rule": {
                    "cidr_blocks": ["10.0.0.0/16"],
                },
                "azure_service_endpoint_rule": {
                    "target_region": ["us-east-1"],
                },
            },
        },
    },
]
