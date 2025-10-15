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

import cartography.intel.azure.rbac
import cartography.intel.azure.subscription
import cartography.intel.azure.tenant
import cartography.intel.entra.groups
import cartography.intel.entra.service_principals
import cartography.intel.entra.users
from tests.data.azure.rbac import AZURE_ROLE_ASSIGNMENTS
from tests.data.azure.rbac import AZURE_ROLE_DEFINITIONS
from tests.data.azure.rbac import ENTRA_GROUPS
from tests.data.azure.rbac import ENTRA_SERVICE_PRINCIPALS
from tests.data.azure.rbac import ENTRA_USERS
from tests.data.azure.rbac import MOCK_ENTRA_TENANT
from tests.integration.cartography.intel.azure.common import (
    create_test_azure_subscription,
)
from tests.integration.cartography.intel.entra.common import create_test_entra_tenant
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "12345678-1234-1234-1234-123456789012"
TEST_TENANT_ID = "tenant-123"
TEST_UPDATE_TAG = 123456789


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


@patch.object(
    cartography.intel.entra.groups,
    "get_group_owners",
    return_value=async_return_empty_list(),
)
@patch.object(
    cartography.intel.entra.groups,
    "get_group_members",
    return_value=async_return_empty_tuple(),
)
@patch.object(
    cartography.intel.entra.groups,
    "get_entra_groups",
    return_value=async_generator_from_list(ENTRA_GROUPS),
)
@patch.object(
    cartography.intel.entra.users,
    "get_tenant",
    return_value=MOCK_ENTRA_TENANT,
)
@patch.object(
    cartography.intel.entra.users,
    "get_users",
    return_value=async_generator_from_list(ENTRA_USERS),
)
@patch.object(
    cartography.intel.entra.service_principals,
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
    await cartography.intel.entra.users.sync_entra_users(
        neo4j_session,
        TEST_TENANT_ID,
        "client-id",
        "client-secret",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # 2. Sync Entra Groups
    await cartography.intel.entra.groups.sync_entra_groups(
        neo4j_session,
        TEST_TENANT_ID,
        "client-id",
        "client-secret",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # 3. Sync Entra Service Principals
    await cartography.intel.entra.service_principals.sync_service_principals(
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
