from copy import deepcopy

from cartography.intel.azure.management_groups import transform_azure_management_groups
from tests.data.azure.management_groups import EXPANDED_PARENT_MANAGEMENT_GROUP
from tests.data.azure.management_groups import TEST_CHILD_MANAGEMENT_GROUP_ID
from tests.data.azure.management_groups import TEST_PARENT_MANAGEMENT_GROUP_ID
from tests.data.azure.management_groups import TEST_TENANT_ID


def test_transform_azure_management_groups_preserves_root_and_child_hierarchy():
    # Arrange
    root_management_group = deepcopy(EXPANDED_PARENT_MANAGEMENT_GROUP)

    nested_child = root_management_group["children"][0]
    nested_child["tenantId"] = None
    nested_child["details"] = None

    # Act
    transformed = transform_azure_management_groups(
        [root_management_group],
    )

    # Assert
    assert len(transformed) == 2

    transformed_by_id = {
        management_group["id"]: management_group for management_group in transformed
    }

    assert set(transformed_by_id) == {
        TEST_PARENT_MANAGEMENT_GROUP_ID,
        TEST_CHILD_MANAGEMENT_GROUP_ID,
    }

    parent = transformed_by_id[TEST_PARENT_MANAGEMENT_GROUP_ID]
    assert parent["name"] == "test-management-group"
    assert parent["tenantId"] == TEST_TENANT_ID
    assert parent["parent_tenant_id"] == TEST_TENANT_ID
    assert parent["parent_management_group_id"] is None

    child = transformed_by_id[TEST_CHILD_MANAGEMENT_GROUP_ID]
    assert child["name"] == "test-child-mgmt-group"
    assert child["displayName"] == "test-child-mgmt-group"
    assert child["tenantId"] is None
    assert child["parent_management_group_id"] == TEST_PARENT_MANAGEMENT_GROUP_ID
    assert child["parent_tenant_id"] is None
    assert child["updatedBy"] is None
    assert child["updatedTime"] is None
    assert child["version"] is None
