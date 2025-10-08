from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.event_grid as event_grid
from tests.data.azure.event_grid import MOCK_TOPICS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.event_grid.get_event_grid_topics")
def test_sync_event_grid_topics(mock_get, neo4j_session):
    """
    Test that we can correctly sync Azure Event Grid Topic data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_TOPICS

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
    event_grid.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes
    expected_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.EventGrid/topics/my-test-topic",
            "my-test-topic",
        ),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureEventGridTopic", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert Relationships
    expected_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.EventGrid/topics/my-test-topic",
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureEventGridTopic",
        "id",
        "RESOURCE",
    )
    assert actual_rels == expected_rels
