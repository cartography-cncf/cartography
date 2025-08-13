from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

import cartography.intel.entra.applications
import tests.data.aws.identitycenter
from cartography.intel.entra.applications import sync_entra_applications
from tests.data.entra.applications import MOCK_APP_ROLE_ASSIGNMENTS
from tests.data.entra.applications import MOCK_ENTRA_APPLICATIONS
from tests.data.entra.applications import MOCK_SERVICE_PRINCIPALS
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
        CREATE (t:EntraTenant {id: '02b2b7cc-fb03-4324-bf6b-eb207b39c479'})
        CREATE (u1:EntraUser {id: 'ae4ac864-4433-4ba6-96a6-20f8cffdadcb', display_name: 'Test User 1', user_principal_name: 'test.user1@example.com'})
        CREATE (u2:EntraUser {id: '11dca63b-cb03-4e53-bb75-fa8060285550', display_name: 'Test User 2'})
        CREATE (g1:EntraGroup {id: '11111111-2222-3333-4444-555555555555', display_name: 'Finance Team'})
        CREATE (g2:EntraGroup {id: '22222222-3333-4444-5555-666666666666', display_name: 'HR Team'})
        CREATE (t)-[:RESOURCE]->(u1)
        CREATE (t)-[:RESOURCE]->(u2)
        CREATE (t)-[:RESOURCE]->(g1)
        CREATE (t)-[:RESOURCE]->(g2)
        """
    )


def _ensure_local_neo4j_has_aws_identity_center(neo4j_session):
    """
    Create AWS Identity Center instance for federation testing.
    """
    # Load AWS Identity Center instance using the existing loader
    import cartography.intel.aws.identitycenter

    cartography.intel.aws.identitycenter.load_identity_center_instances(
        neo4j_session,
        tests.data.aws.identitycenter.LIST_INSTANCES,
        "us-west-2",
        "123456789012",
        "123456789012",
    )


def _ensure_local_neo4j_has_aws_sso_users(neo4j_session):
    """
    Create AWS SSO users for identity federation testing.
    """
    # Load AWS SSO users using the existing loader
    import cartography.intel.aws.identitycenter

    cartography.intel.aws.identitycenter.load_sso_users(
        neo4j_session,
        cartography.intel.aws.identitycenter.transform_sso_users(
            tests.data.aws.identitycenter.LIST_USERS
        ),
        "d-1234567890",  # identity_store_id
        "us-west-2",
        "123456789012",
        TEST_UPDATE_TAG,
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

    return assignments, MOCK_SERVICE_PRINCIPALS


@patch.object(
    cartography.intel.entra.applications,
    "get_app_role_assignments",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.entra.applications,
    "get_entra_applications",
    new_callable=AsyncMock,
    return_value=MOCK_ENTRA_APPLICATIONS,
)
@pytest.mark.asyncio
async def test_sync_entra_applications(mock_get, mock_get_assignments, neo4j_session):
    """
    Ensure that applications actually get loaded and connected to tenant,
    and both user-app and group-app relationships exist
    """
    # Setup mock data with application_app_id and service principals
    mock_get_assignments.return_value = _prepare_mock_assignments()

    # Setup test data - create users, groups, AWS Identity Center, and AWS SSO users for relationship testing
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_aws_identity_center(neo4j_session)
    _ensure_local_neo4j_has_aws_sso_users(neo4j_session)

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

    # Assert Service Principal nodes exist
    expected_service_principal_nodes = {
        (
            "sp-11111111-1111-1111-1111-111111111111",
            "Finance Tracker Service Principal",
        ),
        ("sp-22222222-2222-2222-2222-222222222222", "HR Portal Service Principal"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EntraServicePrincipal",
            ["id", "display_name"],
        )
        == expected_service_principal_nodes
    )

    # Assert Application-Service Principal relationships exist
    expected_app_sp_rels = {
        ("Finance Tracker", "Finance Tracker Service Principal"),
        ("HR Portal", "HR Portal Service Principal"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraApplication",
            "display_name",
            "EntraServicePrincipal",
            "display_name",
            "SERVICE_PRINCIPAL",
        )
        == expected_app_sp_rels
    )

    # Assert Service Principal-AWS Identity Center federation relationships exist
    expected_sp_aws_rels = {
        (
            "Finance Tracker Service Principal",
            "arn:aws:sso:::instance/ssoins-12345678901234567",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraServicePrincipal",
            "display_name",
            "AWSIdentityCenter",
            "id",
            "FEDERATES_TO",
        )
        == expected_sp_aws_rels
    )

    # Assert AWS SSO User nodes exist
    expected_aws_sso_nodes = {
        ("aaaaaaaa-a0d1-aaac-5af0-59c813ec7671", "test.user1@example.com"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "AWSSSOUser",
            ["id", "user_name"],
        )
        == expected_aws_sso_nodes
    )

    # Assert Entra User-AWS SSO User MatchLink relationships exist
    expected_entra_aws_sso_rels = {
        ("test.user1@example.com", "test.user1@example.com"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EntraUser",
            "user_principal_name",
            "AWSSSOUser",
            "user_name",
            "CAN_SIGN_ON_TO",
        )
        == expected_entra_aws_sso_rels
    )
