from unittest.mock import patch

import pytest

import cartography.intel.entra.applications
from cartography.intel.entra.applications import sync_entra_applications
from cartography.intel.entra.users import load_tenant
from tests.data.entra.applications import MOCK_APP_ROLE_ASSIGNMENTS
from tests.data.entra.applications import MOCK_ENTRA_APPLICATIONS
from tests.data.entra.applications import TEST_CLIENT_ID
from tests.data.entra.applications import TEST_CLIENT_SECRET
from tests.data.entra.applications import TEST_TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


def _ensure_local_neo4j_has_test_users(neo4j_session):
    """
    Create test users and groups for integration tests that need them.
    """
    neo4j_session.run(
        """
        CREATE (u1:EntraUser {id: 'ae4ac864-4433-4ba6-96a6-20f8cffdadcb', display_name: 'Test User 1'})
        CREATE (u2:EntraUser {id: '11dca63b-cb03-4e53-bb75-fa8060285550', display_name: 'Test User 2'})
        CREATE (g1:EntraGroup {id: '11111111-2222-3333-4444-555555555555', display_name: 'Finance Team'})
        CREATE (g2:EntraGroup {id: '22222222-3333-4444-5555-666666666666', display_name: 'HR Team'})
        """
    )


def _prepare_mock_assignments():
    """
    Prepare mock app role assignments with the application_app_id attribute.
    This simulates what our get_app_role_assignments function does.
    """
    assignments = []
    app_id_mapping = {
        "Finance Tracker": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "HR Portal": "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb",
    }

    for assignment in MOCK_APP_ROLE_ASSIGNMENTS:
        # Add the application_app_id attribute that our code expects
        assignment.application_app_id = app_id_mapping.get(
            assignment.resource_display_name
        )
        assignments.append(assignment)

    return assignments


async def _mock_get_entra_applications(client):
    """Mock async generator for get_entra_applications"""
    for app in MOCK_ENTRA_APPLICATIONS:
        yield app


async def _mock_get_app_role_assignments_for_app(client, app):
    """Mock async generator for get_app_role_assignments_for_app"""
    # Return assignments that match this app
    assignments = _prepare_mock_assignments()

    for assignment in assignments:
        if assignment.resource_display_name == app.display_name:
            # Convert AppRoleAssignment object to dict to match refactored function
            yield {
                "id": assignment.id,
                "app_role_id": assignment.app_role_id,
                "created_date_time": assignment.created_date_time,
                "principal_id": assignment.principal_id,
                "principal_display_name": assignment.principal_display_name,
                "principal_type": assignment.principal_type,
                "resource_display_name": assignment.resource_display_name,
                "resource_id": assignment.resource_id,
                "application_app_id": assignment.application_app_id,
            }


@patch.object(
    cartography.intel.entra.applications,
    "get_app_role_assignments_for_app",
    side_effect=_mock_get_app_role_assignments_for_app,
)
@patch.object(
    cartography.intel.entra.applications,
    "get_entra_applications",
    side_effect=_mock_get_entra_applications,
)
@pytest.mark.asyncio
async def test_sync_entra_applications(mock_get, mock_get_assignments, neo4j_session):
    """
    Ensure that applications actually get loaded and connected to tenant,
    and both user-app and group-app relationships exist
    """
    # Arrange: Load tenant as prerequisite
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)

    # Setup test data - create users and groups for relationship testing
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    await sync_entra_applications(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert Applications exist
    expected_nodes = {
        ("11111111-1111-1111-1111-111111111111", "Finance Tracker"),
        ("22222222-2222-2222-2222-222222222222", "HR Portal"),
    }
    assert (
        check_nodes(neo4j_session, "EntraApplication", ["id", "display_name"])
        == expected_nodes
    )

    # Assert Applications are connected with Tenant
    expected_rels = {
        ("11111111-1111-1111-1111-111111111111", TEST_TENANT_ID),
        ("22222222-2222-2222-2222-222222222222", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraApplication",
            "id",
            "EntraTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert App Role Assignment nodes exist
    expected_assignment_nodes = {
        ("assignment-1", "User", "Test User 1", "Finance Tracker"),
        ("assignment-2", "User", "Test User 2", "HR Portal"),
        ("assignment-3", "Group", "Finance Team", "Finance Tracker"),
        ("assignment-4", "Group", "HR Team", "HR Portal"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EntraAppRoleAssignment",
            ["id", "principal_type", "principal_display_name", "resource_display_name"],
        )
        == expected_assignment_nodes
    )

    # Assert User-Assignment relationships exist
    expected_user_assignment_rels = {
        ("Test User 1", "assignment-1"),
        ("Test User 2", "assignment-2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraUser",
            "display_name",
            "EntraAppRoleAssignment",
            "id",
            "HAS_APP_ROLE",
        )
        == expected_user_assignment_rels
    )

    # Assert Group-Assignment relationships exist
    expected_group_assignment_rels = {
        ("Finance Team", "assignment-3"),
        ("HR Team", "assignment-4"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraGroup",
            "display_name",
            "EntraAppRoleAssignment",
            "id",
            "HAS_APP_ROLE",
        )
        == expected_group_assignment_rels
    )

    # Assert Assignment-Application relationships exist
    expected_assignment_app_rels = {
        ("assignment-1", "Finance Tracker"),
        ("assignment-2", "HR Portal"),
        ("assignment-3", "Finance Tracker"),
        ("assignment-4", "HR Portal"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraAppRoleAssignment",
            "id",
            "EntraApplication",
            "display_name",
            "ASSIGNED_TO",
        )
        == expected_assignment_app_rels
    )
