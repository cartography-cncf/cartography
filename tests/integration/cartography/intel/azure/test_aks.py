from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.aks as aks
from tests.data.azure.aks import MOCK_AGENT_POOLS
from tests.data.azure.aks import MOCK_CLUSTERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.aks.get_agent_pools")
@patch("cartography.intel.azure.aks.get_aks_clusters")
def test_sync_aks(mock_get_clusters, mock_get_pools, neo4j_session):
    """
    Test that we can correctly sync AKS cluster and agent pool data.
    """
    # Arrange
    mock_get_clusters.return_value = MOCK_CLUSTERS
    mock_get_pools.return_value = MOCK_AGENT_POOLS

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    aks.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Clusters
    expected_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/managedClusters/my-test-aks-cluster",
            "my-test-aks-cluster",
        ),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureKubernetesCluster", ["id", "name"])
    assert actual_nodes == expected_nodes

    expected_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerService/managedClusters/my-test-aks-cluster",
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureKubernetesCluster",
        "id",
        "RESOURCE",
    )
    assert actual_rels == expected_rels

    # Assert Agent Pools
    cluster_id = MOCK_CLUSTERS[0]["id"]
    pool_id = MOCK_AGENT_POOLS[0]["id"]

    expected_pool_nodes = {(pool_id, "agentpool")}
    actual_pool_nodes = check_nodes(
        neo4j_session, "AzureKubernetesAgentPool", ["id", "name"]
    )
    assert actual_pool_nodes == expected_pool_nodes

    expected_pool_rels = {(cluster_id, pool_id)}
    actual_pool_rels = check_rels(
        neo4j_session,
        "AzureKubernetesCluster",
        "id",
        "AzureKubernetesAgentPool",
        "id",
        "HAS_AGENT_POOL",
    )
    assert actual_pool_rels == expected_pool_rels
