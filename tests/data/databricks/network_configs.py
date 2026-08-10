DATABRICKS_NETWORK_VPC_ID = "vpc-0a1b2c3d4e5f6a7b8"
DATABRICKS_NETWORK_SUBNET_IDS = ["subnet-0aaa1111", "subnet-0bbb2222"]
DATABRICKS_NETWORK_SG_IDS = ["sg-0ccc3333"]

DATABRICKS_NETWORK_CONFIGS = [
    {
        "network_id": "net-abc-123",
        "network_name": "prod-vpc-network",
        "account_id": "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed",
        "vpc_id": DATABRICKS_NETWORK_VPC_ID,
        "subnet_ids": DATABRICKS_NETWORK_SUBNET_IDS,
        "security_group_ids": DATABRICKS_NETWORK_SG_IDS,
        "vpc_status": "VALID",
    },
]
