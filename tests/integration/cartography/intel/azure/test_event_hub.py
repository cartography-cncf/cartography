import copy
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.event_hub as event_hub
import cartography.intel.azure.event_hub_namespace as event_hub_namespace
from tests.data.azure.event_hub import MOCK_EVENT_HUBS
from tests.data.azure.event_hub import MOCK_NAMESPACES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


def create_mock_sdk_object(data_dict):
    """
    Creates a MagicMock that simulates an Azure SDK object.
    It has a .as_dict() method and also has attributes for each key.
    """
    # The transforms normalize the payload in place, so hand out a copy to keep the
    # shared fixtures pristine for other tests.
    payload = copy.deepcopy(data_dict)
    mock = MagicMock()
    mock.as_dict.return_value = payload

    # Add attributes to the mock
    for key, value in payload.items():
        setattr(mock, key, value)
    return mock


@patch("cartography.intel.azure.event_hub.get_event_hubs")
@patch("cartography.intel.azure.event_hub_namespace.get_event_hub_namespaces")
def test_sync_event_hub(mock_get_ns, mock_get_eh, neo4j_session):
    """
    Test that we can correctly sync Event Hub Namespace and Event Hub data.
    """
    # Arrange
    mock_get_ns.return_value = [create_mock_sdk_object(ns) for ns in MOCK_NAMESPACES]
    mock_get_eh.return_value = [create_mock_sdk_object(eh) for eh in MOCK_EVENT_HUBS]

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

    mock_client = MagicMock()

    # Act:
    # 1. Sync Namespaces
    namespaces = event_hub_namespace.sync_event_hub_namespaces(
        neo4j_session,
        mock_client,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # 2. Sync Event Hubs
    event_hub.sync_event_hubs(
        neo4j_session,
        mock_client,
        namespaces,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Namespaces. Every property is asserted, not just the identifiers: the
    # fields under the ARM `properties` block are the ones a wrong SDK shape silently
    # drops.
    namespace_id = MOCK_NAMESPACES[0]["id"]
    expected_ns_nodes = {
        (
            namespace_id,
            "my-test-ns",
            "eastus",
            "Standard",
            "Standard",
            "Succeeded",
            True,
            10,
        ),
    }
    actual_ns_nodes = check_nodes(
        neo4j_session,
        "AzureEventHubsNamespace",
        [
            "id",
            "name",
            "location",
            "sku_name",
            "sku_tier",
            "provisioning_state",
            "is_auto_inflate_enabled",
            "maximum_throughput_units",
        ],
    )
    assert actual_ns_nodes == expected_ns_nodes

    expected_ns_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            namespace_id,
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
    event_hub_id = MOCK_EVENT_HUBS[0]["id"]

    expected_eh_nodes = {(event_hub_id, "my-test-eh", "Active", 4, 7)}
    actual_eh_nodes = check_nodes(
        neo4j_session,
        "AzureEventHub",
        ["id", "name", "status", "partition_count", "message_retention_in_days"],
    )
    assert actual_eh_nodes == expected_eh_nodes

    # Test relationship: (Namespace)-[:CONTAINS]->(EventHub)
    expected_eh_contains_rels = {(namespace_id, event_hub_id)}
    actual_eh_contains_rels = check_rels(
        neo4j_session,
        "AzureEventHubsNamespace",
        "id",
        "AzureEventHub",
        "id",
        "CONTAINS",
    )
    assert actual_eh_contains_rels == expected_eh_contains_rels

    # Test relationship: (Subscription)-[:RESOURCE]->(EventHub)
    expected_eh_resource_rels = {(TEST_SUBSCRIPTION_ID, event_hub_id)}
    actual_eh_resource_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureEventHub",
        "id",
        "RESOURCE",
    )
    assert actual_eh_resource_rels == expected_eh_resource_rels
