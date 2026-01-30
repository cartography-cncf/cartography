from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.synapse as synapse
from tests.data.azure.synapse import MOCK_LINKED_SERVICES
from tests.data.azure.synapse import MOCK_MPES
from tests.data.azure.synapse import MOCK_PIPELINES
from tests.data.azure.synapse import MOCK_SPARK_POOLS
from tests.data.azure.synapse import MOCK_SQL_POOLS
from tests.data.azure.synapse import MOCK_WORKSPACES
from tests.data.azure.synapse import TEST_LS_ID
from tests.data.azure.synapse import TEST_MPE_ID
from tests.data.azure.synapse import TEST_PIPELINE_ID
from tests.data.azure.synapse import TEST_SPARK_POOL_ID
from tests.data.azure.synapse import TEST_SQL_POOL_ID
from tests.data.azure.synapse import TEST_WORKSPACE_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"  # Use the short GUID
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.synapse.get_managed_private_endpoints")
@patch("cartography.intel.azure.synapse.get_linked_services")
@patch("cartography.intel.azure.synapse.get_pipelines")
@patch("cartography.intel.azure.synapse.get_spark_pools")
@patch("cartography.intel.azure.synapse.get_dedicated_sql_pools")
@patch("cartography.intel.azure.synapse.get_synapse_workspaces")
def test_sync_synapse(
    mock_get_ws,
    mock_get_sql,
    mock_get_spark,
    mock_get_pipe,
    mock_get_ls,
    mock_get_mpe,
    neo4j_session,
):
    """
    Test that we can correctly sync a Synapse workspace and all its child components.
    """
    # Arrange: Mock all 6 API calls
    mock_get_ws.return_value = MOCK_WORKSPACES
    mock_get_sql.return_value = MOCK_SQL_POOLS
    mock_get_spark.return_value = MOCK_SPARK_POOLS
    mock_get_pipe.return_value = MOCK_PIPELINES
    mock_get_ls.return_value = MOCK_LINKED_SERVICES
    mock_get_mpe.return_value = MOCK_MPES

    # Create the prerequisite AzureSubscription node with the short GUID
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    synapse.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes for all 6 types
    assert check_nodes(neo4j_session, "AzureSynapseWorkspace", ["id"]) == {
        (TEST_WORKSPACE_ID,)
    }
    assert check_nodes(neo4j_session, "AzureSynapseDedicatedSqlPool", ["id"]) == {
        (TEST_SQL_POOL_ID,)
    }
    assert check_nodes(neo4j_session, "AzureSynapseSparkPool", ["id"]) == {
        (TEST_SPARK_POOL_ID,)
    }
    assert check_nodes(neo4j_session, "AzureSynapsePipeline", ["id"]) == {
        (TEST_PIPELINE_ID,)
    }
    assert check_nodes(neo4j_session, "AzureSynapseLinkedService", ["id"]) == {
        (TEST_LS_ID,)
    }
    assert check_nodes(neo4j_session, "AzureSynapseManagedPrivateEndpoint", ["id"]) == {
        (TEST_MPE_ID,)
    }

    # Assert ALL 11 hierarchical relationships
    expected_rels = {
        # Subscription to Workspace (1)
        (TEST_SUBSCRIPTION_ID, TEST_WORKSPACE_ID),
        # Subscription to child nodes (5)
        (TEST_SUBSCRIPTION_ID, TEST_SQL_POOL_ID),
        (TEST_SUBSCRIPTION_ID, TEST_SPARK_POOL_ID),
        (TEST_SUBSCRIPTION_ID, TEST_PIPELINE_ID),
        (TEST_SUBSCRIPTION_ID, TEST_LS_ID),
        (TEST_SUBSCRIPTION_ID, TEST_MPE_ID),
        # Workspace to child nodes (5)
        (TEST_WORKSPACE_ID, TEST_SQL_POOL_ID),
        (TEST_WORKSPACE_ID, TEST_SPARK_POOL_ID),
        (TEST_WORKSPACE_ID, TEST_PIPELINE_ID),
        (TEST_WORKSPACE_ID, TEST_LS_ID),
        (TEST_WORKSPACE_ID, TEST_MPE_ID),
    }

    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureSynapseWorkspace",
        "id",
        "RESOURCE",
    )
    actual_rels.update(
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureSynapseDedicatedSqlPool",
            "id",
            "RESOURCE",
        )
    )
    actual_rels.update(
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureSynapseSparkPool",
            "id",
            "RESOURCE",
        )
    )
    actual_rels.update(
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureSynapsePipeline",
            "id",
            "RESOURCE",
        )
    )
    actual_rels.update(
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureSynapseLinkedService",
            "id",
            "RESOURCE",
        )
    )
    actual_rels.update(
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureSynapseManagedPrivateEndpoint",
            "id",
            "RESOURCE",
        )
    )
    actual_rels.update(
        check_rels(
            neo4j_session,
            "AzureSynapseWorkspace",
            "id",
            "AzureSynapseDedicatedSqlPool",
            "id",
            "CONTAINS",
        )
    )
    actual_rels.update(
        check_rels(
            neo4j_session,
            "AzureSynapseWorkspace",
            "id",
            "AzureSynapseSparkPool",
            "id",
            "CONTAINS",
        )
    )
    actual_rels.update(
        check_rels(
            neo4j_session,
            "AzureSynapseWorkspace",
            "id",
            "AzureSynapsePipeline",
            "id",
            "CONTAINS",
        )
    )
    actual_rels.update(
        check_rels(
            neo4j_session,
            "AzureSynapseWorkspace",
            "id",
            "AzureSynapseLinkedService",
            "id",
            "CONTAINS",
        )
    )
    actual_rels.update(
        check_rels(
            neo4j_session,
            "AzureSynapseWorkspace",
            "id",
            "AzureSynapseManagedPrivateEndpoint",
            "id",
            "CONTAINS",
        )
    )

    assert actual_rels == expected_rels
