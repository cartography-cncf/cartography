from unittest.mock import patch

import pytest

import cartography.intel.microsoft.entra.directory_roles
from cartography.intel.microsoft.entra.directory_roles import sync_entra_directory_roles
from cartography.intel.microsoft.entra.users import load_tenant
from tests.data.microsoft.entra.directory_roles import GLOBAL_ADMIN_ROLE_ID
from tests.data.microsoft.entra.directory_roles import MOCK_ROLE_ASSIGNMENTS
from tests.data.microsoft.entra.directory_roles import MOCK_ROLE_DEFINITIONS
from tests.data.microsoft.entra.directory_roles import TEST_CLIENT_ID
from tests.data.microsoft.entra.directory_roles import TEST_CLIENT_SECRET
from tests.data.microsoft.entra.directory_roles import TEST_GROUP_ID
from tests.data.microsoft.entra.directory_roles import TEST_SP_ID
from tests.data.microsoft.entra.directory_roles import TEST_TENANT_ID
from tests.data.microsoft.entra.directory_roles import TEST_USER_ID
from tests.data.microsoft.entra.directory_roles import USER_ADMIN_ROLE_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


def _ensure_local_neo4j_has_principals(neo4j_session):
    """
    Create the user, group, and service principal that the mock role
    assignments reference, attached to the tenant.
    """
    neo4j_session.run(
        """
        MATCH (t:EntraTenant {id: $tenant_id})
        CREATE (u:EntraUser {id: $user_id, display_name: 'Test User 1'})
        CREATE (g:EntraGroup {id: $group_id, display_name: 'Finance Team'})
        CREATE (sp:EntraServicePrincipal {id: $sp_id, display_name: 'Automation SP'})
        CREATE (t)-[:RESOURCE]->(u)
        CREATE (t)-[:RESOURCE]->(g)
        CREATE (t)-[:RESOURCE]->(sp)
        """,
        {
            "tenant_id": TEST_TENANT_ID,
            "user_id": TEST_USER_ID,
            "group_id": TEST_GROUP_ID,
            "sp_id": TEST_SP_ID,
        },
    )


async def _mock_get_role_definitions(client):
    """Mock for get_role_definitions (returns the full list of definitions)."""
    return list(MOCK_ROLE_DEFINITIONS)


async def _mock_get_role_assignments(client):
    """Mock for get_role_assignments (returns the full list of assignments)."""
    return list(MOCK_ROLE_ASSIGNMENTS)


@patch.object(
    cartography.intel.microsoft.entra.directory_roles,
    "get_role_assignments",
    side_effect=_mock_get_role_assignments,
)
@patch.object(
    cartography.intel.microsoft.entra.directory_roles,
    "get_role_definitions",
    side_effect=_mock_get_role_definitions,
)
@pytest.mark.asyncio
async def test_sync_entra_directory_roles(
    mock_get_definitions, mock_get_assignments, neo4j_session
):
    """
    Ensure directory role definitions and assignments are loaded, connected
    to the tenant, and that each principal type (user, group, service
    principal) is linked to its role assignment and role definition.
    """
    # Arrange
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)
    _ensure_local_neo4j_has_principals(neo4j_session)

    # Act
    await sync_entra_directory_roles(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert - role definition nodes loaded
    assert check_nodes(
        neo4j_session,
        "EntraRoleDefinition",
        ["id", "display_name", "is_built_in"],
    ) == {
        (GLOBAL_ADMIN_ROLE_ID, "Global Administrator", True),
        (USER_ADMIN_ROLE_ID, "User Administrator", True),
    }

    # Assert - role assignment nodes loaded
    assert check_nodes(
        neo4j_session,
        "EntraRoleAssignment",
        ["id", "principal_id", "role_definition_id"],
    ) == {
        ("assignment-ga-user", TEST_USER_ID, GLOBAL_ADMIN_ROLE_ID),
        ("assignment-ua-group", TEST_GROUP_ID, USER_ADMIN_ROLE_ID),
        ("assignment-ga-sp", TEST_SP_ID, GLOBAL_ADMIN_ROLE_ID),
    }

    # Assert - role definitions are resources of the tenant
    assert check_rels(
        neo4j_session,
        "EntraRoleDefinition",
        "id",
        "EntraTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (GLOBAL_ADMIN_ROLE_ID, TEST_TENANT_ID),
        (USER_ADMIN_ROLE_ID, TEST_TENANT_ID),
    }

    # Assert - role assignments are resources of the tenant
    assert check_rels(
        neo4j_session,
        "EntraRoleAssignment",
        "id",
        "EntraTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("assignment-ga-user", TEST_TENANT_ID),
        ("assignment-ua-group", TEST_TENANT_ID),
        ("assignment-ga-sp", TEST_TENANT_ID),
    }

    # Assert - assignment to role definition (ASSIGNED_TO)
    assert check_rels(
        neo4j_session,
        "EntraRoleAssignment",
        "id",
        "EntraRoleDefinition",
        "id",
        "ASSIGNED_TO",
        rel_direction_right=True,
    ) == {
        ("assignment-ga-user", GLOBAL_ADMIN_ROLE_ID),
        ("assignment-ua-group", USER_ADMIN_ROLE_ID),
        ("assignment-ga-sp", GLOBAL_ADMIN_ROLE_ID),
    }

    # Assert - user holds its role assignment (HAS_ROLE)
    assert check_rels(
        neo4j_session,
        "EntraUser",
        "id",
        "EntraRoleAssignment",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {
        (TEST_USER_ID, "assignment-ga-user"),
    }

    # Assert - group holds its role assignment (HAS_ROLE)
    assert check_rels(
        neo4j_session,
        "EntraGroup",
        "id",
        "EntraRoleAssignment",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {
        (TEST_GROUP_ID, "assignment-ua-group"),
    }

    # Assert - service principal holds its role assignment (HAS_ROLE)
    assert check_rels(
        neo4j_session,
        "EntraServicePrincipal",
        "id",
        "EntraRoleAssignment",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {
        (TEST_SP_ID, "assignment-ga-sp"),
    }
