from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.monitor as monitor
from tests.data.azure.monitor import MOCK_METRIC_ALERTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.monitor.get_metric_alerts")
def test_sync_metric_alerts(mock_get, neo4j_session):
    """
    Test that we can correctly sync Azure Monitor Metric Alert data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_METRIC_ALERTS

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
    monitor.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes
    expected_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/CartographyTest-RG/providers/microsoft.insights/metricAlerts/Cartography-Test-Alert",
            "Cartography-Test-Alert",
        ),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureMonitorMetricAlert", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert Relationships
    expected_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/CartographyTest-RG/providers/microsoft.insights/metricAlerts/Cartography-Test-Alert",
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureMonitorMetricAlert",
        "id",
        "HAS_METRIC_ALERT",
    )
    assert actual_rels == expected_rels
