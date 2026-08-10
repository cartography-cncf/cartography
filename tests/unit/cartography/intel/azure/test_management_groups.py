from copy import deepcopy
from types import SimpleNamespace

from cartography.intel.azure import management_groups as management_groups_module
from cartography.intel.azure.management_groups import get_azure_management_groups
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


def test_transform_azure_management_groups_supports_sdk_2_properties_shape():
    # Arrange
    root_management_group = deepcopy(EXPANDED_PARENT_MANAGEMENT_GROUP)
    root_management_group["properties"] = {
        "children": root_management_group.pop("children"),
        "details": root_management_group.pop("details"),
        "displayName": root_management_group.pop("displayName"),
        "tenantId": root_management_group.pop("tenantId"),
    }

    # Act
    transformed = transform_azure_management_groups(
        [root_management_group],
    )

    # Assert
    transformed_by_id = {
        management_group["id"]: management_group for management_group in transformed
    }
    assert set(transformed_by_id) == {
        TEST_PARENT_MANAGEMENT_GROUP_ID,
        TEST_CHILD_MANAGEMENT_GROUP_ID,
    }
    assert transformed_by_id[TEST_PARENT_MANAGEMENT_GROUP_ID]["displayName"] == (
        "test-management-group"
    )
    assert transformed_by_id[TEST_PARENT_MANAGEMENT_GROUP_ID]["tenantId"] == (
        TEST_TENANT_ID
    )
    assert (
        transformed_by_id[TEST_CHILD_MANAGEMENT_GROUP_ID]["parent_management_group_id"]
        == TEST_PARENT_MANAGEMENT_GROUP_ID
    )


def test_get_azure_management_groups_uses_sdk_2_client_name(monkeypatch):
    # Arrange
    credential = object()
    credentials = SimpleNamespace(credential=credential, tenant_id=TEST_TENANT_ID)

    class ManagementGroupsMgmtClient:
        def __init__(self, credential_arg):
            self.credential_arg = credential_arg
            self.management_groups = self

        def get(self, group_id, expand, recurse):
            assert self.credential_arg is credential
            assert group_id == TEST_TENANT_ID
            assert expand == "children"
            assert recurse is True
            return SimpleNamespace(as_dict=lambda: EXPANDED_PARENT_MANAGEMENT_GROUP)

    monkeypatch.setattr(
        management_groups_module,
        "ManagementGroupsMgmtClient",
        ManagementGroupsMgmtClient,
    )

    # Act
    result = get_azure_management_groups(credentials)

    # Assert
    assert result == [EXPANDED_PARENT_MANAGEMENT_GROUP]
