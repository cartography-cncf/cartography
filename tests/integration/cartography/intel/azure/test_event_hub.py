from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.event_hub as event_hub
from tests.data.azure.event_hub import MOCK_EVENT_HUBS
from tests.data.azure.event_hub import MOCK_NAMESPACES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.event_hub.get_event_hubs")
@patch("cartography.intel.azure.event_hub.get_event_hub_namespaces")
def test_sync_event_hub(mock_get_ns, mock_get_eh, neo4j_session):
    """
    Test that we can correctly sync Event Hub Namespace and Event Hub data.
    """
    # Arrange
    mock_get_ns.return_value = MOCK_NAMESPACES
    mock_get_eh.return_value = MOCK_EVENT_HUBS

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
    event_hub.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Namespaces
    expected_ns_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.EventHub/namespaces/my-test-ns",
            "my-test-ns",
        ),
    }
    actual_ns_nodes = check_nodes(
        neo4j_session, "AzureEventHubsNamespace", ["id", "name"]
    )
    assert actual_ns_nodes == expected_ns_nodes

    expected_ns_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.EventHub/namespaces/my-test-ns",
        ),
    }
    actual_ns_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureEventHubsNamespace",
        "id",
        "RESOURCE",
    )
    assert actual_ns_rels == expected_ns_rels

    # Assert Event Hubs
    namespace_id = MOCK_NAMESPACES[0]["id"]
    event_hub_id = MOCK_EVENT_HUBS[0]["id"]

    expected_eh_nodes = {(event_hub_id, "my-test-eh")}
    actual_eh_nodes = check_nodes(neo4j_session, "AzureEventHub", ["id", "name"])
    assert actual_eh_nodes == expected_eh_nodes

    expected_eh_rels = {(namespace_id, event_hub_id)}
    actual_eh_rels = check_rels(
        neo4j_session,
        "AzureEventHubsNamespace",
        "id",
        "AzureEventHub",
        "id",
        "CONTAINS",
    )
    assert actual_eh_rels == expected_eh_rels
