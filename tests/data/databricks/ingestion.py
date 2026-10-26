"""Canned API responses for end-to-end start_databricks_ingestion tests.

Every value is fake. Each workspace maps request URIs to responses; any URI not
listed answers with an empty body or list.
"""

WORKSPACE_A_HOST = "https://dbc-0000000a-0000.cloud.databricks.com"
WORKSPACE_A_ID = "dbc-0000000a-0000.cloud.databricks.com"

CLUSTERS_URI = "/api/2.1/clusters/list"

CLUSTER = {
    "cluster_id": "0000-000000-cluster0",
    "cluster_name": "fake-cluster",
    "state": "TERMINATED",
}
