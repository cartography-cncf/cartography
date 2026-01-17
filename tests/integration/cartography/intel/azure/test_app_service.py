from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.app_service as app_service
from tests.data.azure.app_service import MOCK_APP_SERVICES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.app_service.get_app_services")
def test_sync_app_services(mock_get, neo4j_session):
    """
    Test that we can correctly sync Azure App Service data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_APP_SERVICES

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
    app_service.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes: Ensure only the App Service (and not the function app) was loaded.
    expected_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-test-app-service",
            "my-test-app-service",
        ),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureAppService", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert Relationships
    expected_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Web/sites/my-test-app-service",
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureAppService",
        "id",
        "RESOURCE",
    )
    assert actual_rels == expected_rels
