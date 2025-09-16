from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.functions as functions
from tests.data.azure.functions import MOCK_FUNCTION_APPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.functions.get_function_apps")
def test_sync_function_apps(mock_get, neo4j_session):
    """
    Test that we can correctly sync Azure Function App data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_FUNCTION_APPS

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
    functions.sync(
        neo4j_session,
        MagicMock(),  # credentials object is not used directly by sync as get is mocked
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes: Ensure only the function app (and not the web app) was loaded.
    expected_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-test-func-app",
            "my-test-func-app",
        ),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureFunctionApp", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert Relationships
    expected_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-test-func-app",
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureFunctionApp",
        "id",
        "RESOURCE",
    )
    assert actual_rels == expected_rels
