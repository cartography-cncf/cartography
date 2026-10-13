from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.rbac
from tests.data.azure.rbac import AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS
from tests.data.azure.rbac import AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS_MIXED_SCOPES
from tests.data.azure.rbac import TEST_MANAGEMENT_GROUP_ID

TEST_SUBSCRIPTION_ID = "12345678-1234-1234-1234-123456789012"


class _FakeAzureRoleAssignment:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    def as_dict(self) -> dict[str, Any]:
        return self.data


@patch.object(cartography.intel.azure.rbac, "get_client")
def test_get_role_assignments_for_scope_filters_to_direct_scope(
    mock_get_client,
):
    # Arrange
    mock_client = MagicMock()
    mock_client.role_assignments.list_for_scope.return_value = [
        _FakeAzureRoleAssignment(assignment)
        for assignment in AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS_MIXED_SCOPES
    ]
    mock_get_client.return_value = mock_client

    # Act
    result = cartography.intel.azure.rbac.get_role_assignments_for_scope(
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_MANAGEMENT_GROUP_ID,
    )

    # Assert
    mock_client.role_assignments.list_for_scope.assert_called_once_with(
        TEST_MANAGEMENT_GROUP_ID,
        filter="atScope()",
    )
    assert result == AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS
