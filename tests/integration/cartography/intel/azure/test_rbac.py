"""
Integration test for Azure RBAC module.

This test follows the VPC integration test pattern:
1. Patches all required sync functions' get() methods
2. Calls all respective sync functions to populate the graph
3. Asserts that the expected nodes and relationships are created
"""

from typing import Any
from typing import AsyncGenerator
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from azure.core.exceptions import HttpResponseError

import cartography.intel.azure.rbac
import cartography.intel.azure.subscription
import cartography.intel.azure.tenant
import cartography.intel.microsoft.entra.groups
import cartography.intel.microsoft.entra.service_principals
import cartography.intel.microsoft.entra.users
from tests.data.azure.rbac import AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS
from tests.data.azure.rbac import AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS_MIXED_SCOPES
from tests.data.azure.rbac import AZURE_MANAGEMENT_GROUP_ROLE_DEFINITIONS
from tests.data.azure.rbac import AZURE_ROLE_ASSIGNMENTS
from tests.data.azure.rbac import AZURE_ROLE_DEFINITIONS
from tests.data.azure.rbac import ENTRA_GROUPS
from tests.data.azure.rbac import ENTRA_SERVICE_PRINCIPALS
from tests.data.azure.rbac import ENTRA_USERS
from tests.data.azure.rbac import MOCK_ENTRA_TENANT
from tests.data.azure.rbac import TEST_MANAGEMENT_GROUP_ID
from tests.integration.cartography.intel.azure.common import (
    create_test_azure_subscription,
)
from tests.integration.cartography.intel.microsoft.entra.common import (
    create_test_entra_tenant,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "12345678-1234-1234-1234-123456789012"
TEST_TENANT_ID = "tenant-123"
TEST_UPDATE_TAG = 123456789
TEST_MANAGEMENT_GROUP_ROLE_ASSIGNMENT_ID = AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS[0][
    "id"
]


async def async_generator_from_list(items: list[Any]) -> AsyncGenerator[Any, None]:
    """Helper function to create an async generator from a list for mocking purposes."""
    for item in items:
        yield item


async def async_return_empty_list():
    """Helper function to return an empty list asynchronously."""
    return []


async def async_return_empty_tuple():
    """Helper function to return an empty tuple asynchronously."""
    return ([], [])


def _create_test_azure_management_group(neo4j_session) -> None:
    neo4j_session.run(
        """
        MERGE (t:AzureTenant {id: $tenant_id})
        SET t.lastupdated = $update_tag
        MERGE (mg:AzureManagementGroup {id: $management_group_id})
        SET mg.name = 'test-management-group',
            mg.lastupdated = $update_tag
        MERGE (t)-[r:RESOURCE]->(mg)
        SET r.lastupdated = $update_tag
        """,
        tenant_id=TEST_TENANT_ID,
        management_group_id=TEST_MANAGEMENT_GROUP_ID,
        update_tag=TEST_UPDATE_TAG,
    )


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


@patch.object(
    cartography.intel.microsoft.entra.groups,
    "get_group_owners",
    return_value=async_return_empty_list(),
)
@patch.object(
    cartography.intel.microsoft.entra.groups,
    "get_group_members",
    return_value=async_return_empty_tuple(),
)
@patch.object(
    cartography.intel.microsoft.entra.groups,
    "get_entra_groups",
    return_value=async_generator_from_list(ENTRA_GROUPS),
)
@patch.object(
    cartography.intel.microsoft.entra.users,
    "get_tenant",
    return_value=MOCK_ENTRA_TENANT,
)
@patch.object(
    cartography.intel.microsoft.entra.users,
    "get_users",
    return_value=async_generator_from_list(ENTRA_USERS),
)
@patch.object(
    cartography.intel.microsoft.entra.service_principals,
    "get_entra_service_principals",
    return_value=async_generator_from_list(ENTRA_SERVICE_PRINCIPALS),
)
@patch.object(
    cartography.intel.azure.rbac,
    "get_role_assignments",
    return_value=AZURE_ROLE_ASSIGNMENTS,
)
@patch.object(
    cartography.intel.azure.rbac,
    "get_role_definitions_by_ids",
    return_value=AZURE_ROLE_DEFINITIONS,
)
@pytest.mark.asyncio
async def test_sync_azure_rbac(
    mock_get_role_definitions,
    mock_get_role_assignments,
    mock_get_entra_service_principals,
    mock_get_users,
    mock_get_tenant,
    mock_get_entra_groups,
    mock_get_group_members,
    mock_get_group_owners,
    neo4j_session,
):
    """
    Test that Azure RBAC sync creates the expected nodes and relationships.
    """
    # Create test subscription and tenant
    create_test_azure_subscription(neo4j_session, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG)
    create_test_entra_tenant(neo4j_session, TEST_TENANT_ID, TEST_UPDATE_TAG)

    # Mock credentials
    mock_credentials = MagicMock()

    # Common job parameters
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # 1. Sync Entra Users
    await cartography.intel.microsoft.entra.users.sync_entra_users(
        neo4j_session,
        TEST_TENANT_ID,
        "client-id",
        "client-secret",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # 2. Sync Entra Groups
    await cartography.intel.microsoft.entra.groups.sync_entra_groups(
        neo4j_session,
        TEST_TENANT_ID,
        "client-id",
        "client-secret",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # 3. Sync Entra Service Principals
    await cartography.intel.microsoft.entra.service_principals.sync_service_principals(
        neo4j_session,
        TEST_TENANT_ID,
        "client-id",
        "client-secret",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # 4. Sync Azure RBAC
    cartography.intel.azure.rbac.sync(
        neo4j_session,
        mock_credentials,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check that expected nodes are created

    # Check Entra users
    assert check_nodes(neo4j_session, "EntraUser", ["id"]) == {
        ("user-123",),
        ("user-456",),
    }

    # Check Entra groups
    assert check_nodes(neo4j_session, "EntraGroup", ["id"]) == {
        ("group-789",),
    }

    # Check Entra service principals
    assert check_nodes(neo4j_session, "EntraServicePrincipal", ["id"]) == {
        ("sp-101",),
    }

    # Check Azure role assignments
    assert check_nodes(neo4j_session, "AzureRoleAssignment", ["id"]) == {
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-1",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-2",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-3",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-4",
        ),
    }

    # Check Azure role definitions
    assert check_nodes(neo4j_session, "AzureRoleDefinition", ["id"]) == {
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/9b7fa4d4-9aa6-4d26-9dfc-4ef0b805d5d4",
        ),
    }

    # Check Azure permissions
    assert check_nodes(neo4j_session, "AzurePermissions", ["id"]) == {
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635/permissions/0",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7/permissions/0",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/9b7fa4d4-9aa6-4d26-9dfc-4ef0b805d5d4/permissions/0",
        ),
    }

    # Assert - Check that expected relationships are created

    # Check role assignment to role definition relationships
    assert check_rels(
        neo4j_session,
        "AzureRoleAssignment",
        "id",
        "AzureRoleDefinition",
        "id",
        "ROLE_ASSIGNED",
        rel_direction_right=True,
    ) == {
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-1",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-2",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/9b7fa4d4-9aa6-4d26-9dfc-4ef0b805d5d4",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-3",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-4",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",
        ),
    }
    # Check role assignment to principal relationships
    assert check_rels(
        neo4j_session,
        "AzureRoleAssignment",
        "id",
        "EntraUser",
        "id",
        "HAS_ROLE_ASSIGNMENT",
        rel_direction_right=False,
    ) == {
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-1",
            "user-123",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-3",
            "user-456",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AzureRoleAssignment",
        "id",
        "EntraGroup",
        "id",
        "HAS_ROLE_ASSIGNMENT",
        rel_direction_right=False,
    ) == {
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-2",
            "group-789",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AzureRoleAssignment",
        "id",
        "EntraServicePrincipal",
        "id",
        "HAS_ROLE_ASSIGNMENT",
        rel_direction_right=False,
    ) == {
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-4",
            "sp-101",
        ),
    }

    # Check role definition to permissions relationships
    assert check_rels(
        neo4j_session,
        "AzureRoleDefinition",
        "id",
        "AzurePermissions",
        "id",
        "HAS_PERMISSIONS",
        rel_direction_right=True,
    ) == {
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635/permissions/0",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7/permissions/0",
        ),
        (
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/9b7fa4d4-9aa6-4d26-9dfc-4ef0b805d5d4",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleDefinitions/9b7fa4d4-9aa6-4d26-9dfc-4ef0b805d5d4/permissions/0",
        ),
    }

    # Check subscription relationships
    assert check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureRoleAssignment",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "12345678-1234-1234-1234-123456789012",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-1",
        ),
        (
            "12345678-1234-1234-1234-123456789012",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-2",
        ),
        (
            "12345678-1234-1234-1234-123456789012",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-3",
        ),
        (
            "12345678-1234-1234-1234-123456789012",
            "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments/assignment-4",
        ),
    }


@patch.object(
    cartography.intel.azure.rbac,
    "get_role_assignments_for_scope",
    return_value=AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS,
)
@patch.object(
    cartography.intel.azure.rbac,
    "get_role_definitions_by_ids",
    return_value=AZURE_MANAGEMENT_GROUP_ROLE_DEFINITIONS,
)
def test_sync_management_group_role_assignments(
    mock_get_role_definitions,
    mock_get_role_assignments_for_scope,
    neo4j_session,
):
    # Arrange
    create_test_azure_subscription(neo4j_session, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG)
    _create_test_azure_management_group(neo4j_session)
    neo4j_session.run(
        """
        MERGE (u:EntraUser {id: 'user-123'})
        SET u.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }
    mock_credentials = MagicMock()

    # Act
    cartography.intel.azure.rbac.sync_management_group_role_assignments(
        neo4j_session,
        mock_credentials,
        TEST_MANAGEMENT_GROUP_ID,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert
    mock_get_role_definitions.assert_called_once_with(
        mock_credentials,
        TEST_SUBSCRIPTION_ID,
        [AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS[0]["role_definition_id"]],
        stamp_subscription_id=False,
    )
    assert (TEST_MANAGEMENT_GROUP_ROLE_ASSIGNMENT_ID,) in check_nodes(
        neo4j_session,
        "AzureRoleAssignment",
        ["id"],
    )

    assert check_rels(
        neo4j_session,
        "AzureManagementGroup",
        "id",
        "AzureRoleAssignment",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_MANAGEMENT_GROUP_ID,
            TEST_MANAGEMENT_GROUP_ROLE_ASSIGNMENT_ID,
        ),
    }

    assert (
        TEST_SUBSCRIPTION_ID,
        TEST_MANAGEMENT_GROUP_ROLE_ASSIGNMENT_ID,
    ) not in check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureRoleAssignment",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )

    assert (
        TEST_MANAGEMENT_GROUP_ROLE_ASSIGNMENT_ID,
        AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS[0]["role_definition_id"],
    ) in check_rels(
        neo4j_session,
        "AzureRoleAssignment",
        "id",
        "AzureRoleDefinition",
        "id",
        "ROLE_ASSIGNED",
        rel_direction_right=True,
    )

    assert (
        TEST_SUBSCRIPTION_ID,
        AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS[0]["role_definition_id"],
    ) not in check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureRoleDefinition",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )

    assert (
        AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS[0]["role_definition_id"],
        f"{AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS[0]['role_definition_id']}/permissions/0",
    ) in check_rels(
        neo4j_session,
        "AzureRoleDefinition",
        "id",
        "AzurePermissions",
        "id",
        "HAS_PERMISSIONS",
        rel_direction_right=True,
    )

    assert (
        TEST_SUBSCRIPTION_ID,
        f"{AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS[0]['role_definition_id']}/permissions/0",
    ) not in check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzurePermissions",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )

    assert (
        TEST_MANAGEMENT_GROUP_ROLE_ASSIGNMENT_ID,
        "user-123",
    ) in check_rels(
        neo4j_session,
        "AzureRoleAssignment",
        "id",
        "EntraUser",
        "id",
        "HAS_ROLE_ASSIGNMENT",
        rel_direction_right=False,
    )


@patch.object(
    cartography.intel.azure.rbac,
    "get_role_assignments_for_scope",
)
@patch.object(
    cartography.intel.azure.rbac,
    "get_role_definitions_by_ids",
    return_value=AZURE_ROLE_DEFINITIONS,
)
def test_cleanup_stale_management_group_role_assignments(
    mock_get_role_definitions,
    mock_get_role_assignments_for_scope,
    neo4j_session,
):
    # Arrange
    _create_test_azure_management_group(neo4j_session)
    first_common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }
    mock_get_role_assignments_for_scope.return_value = (
        AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS
    )
    cartography.intel.azure.rbac.sync_management_group_role_assignments(
        neo4j_session,
        MagicMock(),
        TEST_MANAGEMENT_GROUP_ID,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        first_common_job_parameters,
    )

    second_update_tag = TEST_UPDATE_TAG + 1
    second_common_job_parameters = {
        "UPDATE_TAG": second_update_tag,
        "TENANT_ID": TEST_TENANT_ID,
    }
    mock_get_role_assignments_for_scope.return_value = []

    # Act
    cartography.intel.azure.rbac.sync_management_group_role_assignments(
        neo4j_session,
        MagicMock(),
        TEST_MANAGEMENT_GROUP_ID,
        TEST_SUBSCRIPTION_ID,
        second_update_tag,
        second_common_job_parameters,
    )

    # Assert
    assert (TEST_MANAGEMENT_GROUP_ROLE_ASSIGNMENT_ID,) not in check_nodes(
        neo4j_session,
        "AzureRoleAssignment",
        ["id"],
    )


@patch.object(
    cartography.intel.azure.rbac,
    "get_role_assignments_for_scope",
)
@patch.object(
    cartography.intel.azure.rbac,
    "get_role_definitions_by_ids",
    return_value=AZURE_ROLE_DEFINITIONS,
)
def test_management_group_role_assignment_access_loss_preserves_existing_assignments(
    mock_get_role_definitions,
    mock_get_role_assignments_for_scope,
    neo4j_session,
):
    # Arrange
    _create_test_azure_management_group(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
    }
    mock_get_role_assignments_for_scope.return_value = (
        AZURE_MANAGEMENT_GROUP_ROLE_ASSIGNMENTS
    )
    cartography.intel.azure.rbac.sync_management_group_role_assignments(
        neo4j_session,
        MagicMock(),
        TEST_MANAGEMENT_GROUP_ID,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    mock_get_role_assignments_for_scope.side_effect = HttpResponseError(
        message="management group role assignment lookup failed",
    )

    # Act
    cartography.intel.azure.rbac.sync_management_group_role_assignments_for_management_groups(
        neo4j_session,
        MagicMock(),
        [{"id": TEST_MANAGEMENT_GROUP_ID}],
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG + 1,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG + 1,
            "TENANT_ID": TEST_TENANT_ID,
        },
    )

    # Assert
    assert (TEST_MANAGEMENT_GROUP_ROLE_ASSIGNMENT_ID,) in check_nodes(
        neo4j_session,
        "AzureRoleAssignment",
        ["id"],
    )
