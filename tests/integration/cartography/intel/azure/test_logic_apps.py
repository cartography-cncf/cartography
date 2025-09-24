from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.logic_apps as logic_apps
from tests.data.azure.logic_apps import MOCK_LOGIC_APPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.logic_apps.get_logic_apps")
def test_sync_logic_apps(mock_get, neo4j_session):
    """
    Test that we can correctly sync Azure Logic App data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_LOGIC_APPS

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
    logic_apps.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes
    expected_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Logic/workflows/my-test-logic-app",
            "my-test-logic-app",
        ),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureLogicApp", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert Relationships
    expected_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Logic/workflows/my-test-logic-app",
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureLogicApp",
        "id",
        "RESOURCE",
    )
    assert actual_rels == expected_rels
