"""Canned API responses for end-to-end start_databricks_ingestion tests.

Every value is fake. Each workspace maps request URIs to responses; any URI not
listed answers with an empty body or list.
"""

WORKSPACE_A_HOST = "https://dbc-0000000a-0000.cloud.databricks.com"
WORKSPACE_A_ID = "1000000000000001"
WORKSPACE_B_HOST = "https://dbc-0000000b-0000.cloud.databricks.com"
WORKSPACE_B_ID = "1000000000000002"
# What the workspace API reports in its x-databricks-org-id response header.
WORKSPACE_IDS_BY_HOST = {
    WORKSPACE_A_HOST: WORKSPACE_A_ID,
    WORKSPACE_B_HOST: WORKSPACE_B_ID,
}
METASTORE_ID = "00000000-0000-0000-0000-000000000001"

CLUSTERS_URI = "/api/2.1/clusters/list"
USERS_URI = "/api/2.0/preview/scim/v2/Users"
METASTORE_SUMMARY_URI = "/api/2.1/unity-catalog/metastore_summary"
METASTORE_ASSIGNMENT_URI = "/api/2.1/unity-catalog/current-metastore-assignment"
CATALOGS_URI = "/api/2.1/unity-catalog/catalogs"

CLUSTER = {
    "cluster_id": "0000-000000-cluster0",
    "cluster_name": "fake-cluster",
    "state": "TERMINATED",
}

USER = {"id": "1000", "userName": "analyst@example.com", "active": True}

METASTORE_RESPONSES = {
    METASTORE_SUMMARY_URI: {"metastore_id": METASTORE_ID, "name": "fake-metastore"},
    METASTORE_ASSIGNMENT_URI: {"metastore_id": METASTORE_ID},
}


def catalog(name: str) -> dict:
    return {"metastore_id": METASTORE_ID, "name": name, "full_name": name}


def catalog_grant_uri(name: str) -> str:
    return f"/api/2.1/unity-catalog/permissions/catalog/{name}"


CATALOG_GRANT = [{"principal": USER["userName"], "privileges": ["USE_CATALOG"]}]
