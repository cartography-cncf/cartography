from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.management_groups as management_groups
from tests.data.azure.management_groups import AZURE_MANAGEMENT_GROUPS
from tests.data.azure.management_groups import TEST_CHILD_MANAGEMENT_GROUP_ID
from tests.data.azure.management_groups import TEST_PARENT_MANAGEMENT_GROUP_ID
from tests.data.azure.management_groups import TEST_TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.management_groups.get_azure_management_groups")
def test_sync_management_groups_happy_path(
    mock_get,
    neo4j_session,
):
    """
    Test that we can correctly sync Azure management groups and hierarchy relationships.
    """
    # Arrange
    mock_get.return_value = AZURE_MANAGEMENT_GROUPS

    neo4j_session.run(
        """
        MERGE (t:AzureTenant{id: $tenant_id})
        SET t.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }

    # Act
    management_groups.sync(
        neo4j_session,
        MagicMock(),
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert
    actual_nodes = check_nodes(
        neo4j_session,
        "AzureManagementGroup",
        ["id", "name"],
    )
    assert actual_nodes == {
        (TEST_PARENT_MANAGEMENT_GROUP_ID, "test-management-group"),
        (TEST_CHILD_MANAGEMENT_GROUP_ID, "test-child-mgmt-group"),
    }

    tenant_resource_rels = check_rels(
        neo4j_session,
        "AzureTenant",
        "id",
        "AzureManagementGroup",
        "id",
        "RESOURCE",
    )
    assert tenant_resource_rels == {
        (TEST_TENANT_ID, TEST_PARENT_MANAGEMENT_GROUP_ID),
        (TEST_TENANT_ID, TEST_CHILD_MANAGEMENT_GROUP_ID),
    }

    management_group_parent_rels = check_rels(
        neo4j_session,
        "AzureManagementGroup",
        "id",
        "AzureManagementGroup",
        "id",
        "PARENT",
    )
    assert management_group_parent_rels == {
        (TEST_CHILD_MANAGEMENT_GROUP_ID, TEST_PARENT_MANAGEMENT_GROUP_ID),
    }

    tenant_parent_rels = check_rels(
        neo4j_session,
        "AzureManagementGroup",
        "id",
        "AzureTenant",
        "id",
        "PARENT",
    )
    assert tenant_parent_rels == {
        (TEST_PARENT_MANAGEMENT_GROUP_ID, TEST_TENANT_ID),
    }
