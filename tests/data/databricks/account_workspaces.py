DATABRICKS_ACCOUNT_WORKSPACES = [
    {
        "workspace_id": 1234567890123456,
        "workspace_name": "prod",
        "deployment_name": "dbc-aaeaddda-e52f",
    },
    {
        "workspace_id": 6543210987654321,
        "workspace_name": "staging",
        "deployment_name": "dbc-bbfbeeeb-f63a",
    },
]

# Numeric workspace id (as str) -> deployment-host node id.
DATABRICKS_ACCOUNT_WORKSPACE_NODE_IDS = {
    "1234567890123456": "dbc-aaeaddda-e52f.cloud.databricks.com",
    "6543210987654321": "dbc-bbfbeeeb-f63a.cloud.databricks.com",
}
