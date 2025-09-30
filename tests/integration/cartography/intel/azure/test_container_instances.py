from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.container_instances as container_instances
from tests.data.azure.container_instances import MOCK_CONTAINER_GROUPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.container_instances.get_container_instances")
def test_sync_container_instances(mock_get, neo4j_session):
    """
    Test that we can correctly sync Azure Container Instance data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_CONTAINER_GROUPS

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
    container_instances.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes
    expected_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerInstance/containerGroups/my-test-aci",
            "my-test-aci",
        ),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureContainerInstance", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert Relationships
    expected_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.ContainerInstance/containerGroups/my-test-aci",
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureContainerInstance",
        "id",
        "RESOURCE",
    )
    assert actual_rels == expected_rels
