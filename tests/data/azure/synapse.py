TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_RESOURCE_GROUP_NAME = "Cartography-Synapse-Test-RG"
TEST_WORKSPACE_NAME = "carto-test-synapse-ws"
TEST_WORKSPACE_ID = f"/subscriptions/{TEST_SUBSCRIPTION_ID}/resourceGroups/{TEST_RESOURCE_GROUP_NAME}/providers/Microsoft.Synapse/workspaces/{TEST_WORKSPACE_NAME}"
TEST_SQL_POOL_ID = f"{TEST_WORKSPACE_ID}/sqlPools/carto-sql-pool"
TEST_SPARK_POOL_ID = f"{TEST_WORKSPACE_ID}/bigDataPools/carto-spark-pool"
TEST_PIPELINE_ID = f"{TEST_WORKSPACE_ID}/pipelines/carto-dummy-pipeline"
TEST_LS_ID = f"{TEST_WORKSPACE_ID}/linkedservices/carto-ls-to-storage"
TEST_MPE_ID = f"{TEST_WORKSPACE_ID}/managedVirtualNetworks/default/managedPrivateEndpoints/carto-mpe-to-storage"

# Mock response for `client.workspaces.list()`
MOCK_WORKSPACES = [
    {
        "id": TEST_WORKSPACE_ID,
        "name": TEST_WORKSPACE_NAME,
        "location": "eastus",
        "connectivity_endpoints": {
            "dev": f"https://{TEST_WORKSPACE_NAME}.dev.azuresynapse.net",
            "sql": f"https://{TEST_WORKSPACE_NAME}.sql.azuresynapse.net",
        },
    },
]

# Mock response for `client.sql_pools.list_by_workspace()`
MOCK_SQL_POOLS = [
    {
        "id": TEST_SQL_POOL_ID,
        "name": "carto-sql-pool",
        "location": "eastus",
        "properties": {"provisioningState": "Succeeded"},
        "sku": {"name": "DW100c"},
    },
]

# Mock response for `client.big_data_pools.list_by_workspace()`
MOCK_SPARK_POOLS = [
    {
        "id": TEST_SPARK_POOL_ID,
        "name": "carto-spark-pool",
        "location": "eastus",
        "properties": {
            "provisioning_state": "Succeeded",
            "node_size": "Small",
            "node_count": 3,
            "spark_version": "3.3",
        },
    },
]

# Mock response for `artifacts_client.pipeline.get_pipelines_by_workspace()`
MOCK_PIPELINES = [
    {
        "id": TEST_PIPELINE_ID,
        "name": "carto-dummy-pipeline",
    },
]

# Mock response for `artifacts_client.linked_service.get_linked_services_by_workspace()`
MOCK_LINKED_SERVICES = [
    {
        "id": TEST_LS_ID,
        "name": "carto-ls-to-storage",
    },
]

# Mock response for `client.managed_private_endpoints.list()`
MOCK_MPES = [
    {
        "id": TEST_MPE_ID,
        "name": "carto-mpe-to-storage",
        "properties": {
            "privateLinkResourceId": "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Storage/storageAccounts/teststorage",
        },
    },
]
