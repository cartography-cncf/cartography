from unittest.mock import patch

import cartography.intel.azure.compute
from tests.data.azure.compute import DESCRIBE_DISKS
from tests.data.azure.compute import DESCRIBE_SNAPSHOTS
from tests.data.azure.compute import DESCRIBE_VMS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_RESOURCE_GROUP = "TestRG"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.azure.compute,
    "get_snapshots_list",
    return_value=DESCRIBE_SNAPSHOTS,
)
@patch.object(
    cartography.intel.azure.compute,
    "get_disks",
    return_value=DESCRIBE_DISKS,
)
@patch.object(
    cartography.intel.azure.compute,
    "get_vm_list",
    return_value=DESCRIBE_VMS,
)
def test_sync_compute_resources(
    mock_get_vms,
    mock_get_disks,
    mock_get_snapshots,
    neo4j_session,
):
    """
    Test that compute resources (VMs, disks, snapshots) sync correctly
    via the main sync() function
    """
    # Arrange - Create subscription
    neo4j_session.run(
        """
        MERGE (as:AzureSubscription{id: $subscription_id})
        ON CREATE SET as.firstseen = timestamp()
        SET as.lastupdated = $update_tag
        """,
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act - Call the main sync function
    cartography.intel.azure.compute.sync(
        neo4j_session,
        credentials=None,  # Mocked - not used
        subscription_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters={
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
        },
    )

    # Assert - Check VMs were created
    expected_vm_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
        ),
    }
    assert (
        check_nodes(neo4j_session, "AzureVirtualMachine", ["id"]) == expected_vm_nodes
    )

    # Assert - Check disks were created
    expected_disk_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd0",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd1",
        ),
    }
    assert check_nodes(neo4j_session, "AzureDisk", ["id"]) == expected_disk_nodes

    # Assert - Check snapshots were created
    expected_snapshot_nodes = {
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss0",
        ),
        (
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss1",
        ),
    }
    assert (
        check_nodes(neo4j_session, "AzureSnapshot", ["id"]) == expected_snapshot_nodes
    )

    # Assert - Check VM-to-subscription relationships
    expected_vm_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/virtualMachines/TestVM1",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureVirtualMachine",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_vm_rels
    )

    # Assert - Check disk-to-subscription relationships
    expected_disk_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd0",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/disks/dd1",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureDisk",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_disk_rels
    )

    # Assert - Check snapshot-to-subscription relationships
    expected_snapshot_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss0",
        ),
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/resourceGroups/TestRG/providers/Microsoft.Compute/snapshots/ss1",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AzureSubscription",
            "id",
            "AzureSnapshot",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_snapshot_rels
    )
