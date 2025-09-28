from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.resource_groups as resource_groups
from tests.data.azure.resource_group import MOCK_RESOURCE_GROUPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.resource_groups.get_resource_groups")
def test_sync_resource_groups(mock_get, neo4j_session):
    """
    Test that we can correctly sync Azure Resource Group data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_RESOURCE_GROUPS

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
    resource_groups.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes
    expected_nodes = {
        ("/subscriptions/00-00-00-00/resourceGroups/TestRG1", "TestRG1"),
        ("/subscriptions/00-00-00-00/resourceGroups/TestRG2", "TestRG2"),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureResourceGroup", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert Relationships
    expected_rels = {
        (TEST_SUBSCRIPTION_ID, "/subscriptions/00-00-00-00/resourceGroups/TestRG1"),
        (TEST_SUBSCRIPTION_ID, "/subscriptions/00-00-00-00/resourceGroups/TestRG2"),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureResourceGroup",
        "id",
        "RESOURCE",
    )
    assert actual_rels == expected_rels
