from unittest.mock import patch

import pytest

import cartography.client.core.tx
import cartography.intel.aws.identitycenter
import cartography.intel.microsoft.entra.app_role_assignments
import cartography.intel.microsoft.entra.applications
import cartography.intel.microsoft.entra.service_principals
import cartography.util
import tests.data.aws.identitycenter
from cartography.analysis.microsoft.entra.analysis import ENTRA_APPLICATION_PROJECTION
from cartography.intel.microsoft.entra.app_role_assignments import (
    sync_app_role_assignments,
)
from cartography.intel.microsoft.entra.applications import sync_entra_applications
from cartography.intel.microsoft.entra.federation.aws_identity_center import (
    sync_entra_federation,
)
from cartography.intel.microsoft.entra.service_principals import sync_service_principals
from cartography.intel.microsoft.entra.users import load_tenant
from tests.data.microsoft.entra.applications import MOCK_APP_ROLE_ASSIGNMENTS
from tests.data.microsoft.entra.applications import MOCK_ENTRA_APPLICATIONS
from tests.data.microsoft.entra.applications import MOCK_SERVICE_PRINCIPALS
from tests.data.microsoft.entra.applications import TEST_CLIENT_ID
from tests.data.microsoft.entra.applications import TEST_CLIENT_SECRET
from tests.data.microsoft.entra.applications import TEST_TENANT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 1234567890


def _ensure_local_neo4j_has_test_users(neo4j_session):
    """
    Create test users and groups for integration tests that need them.
    """
    neo4j_session.run(
        """
        MATCH (t:EntraTenant {id: $tenant_id})
        CREATE (u1:EntraUser {id: 'ae4ac864-4433-4ba6-96a6-20f8cffdadcb', display_name: 'Test User 1', user_principal_name: 'test.user1@example.com'})
        CREATE (u2:EntraUser {id: '11dca63b-cb03-4e53-bb75-fa8060285550', display_name: 'Test User 2'})
        CREATE (g1:EntraGroup {id: '11111111-2222-3333-4444-555555555555', display_name: 'Finance Team'})
        CREATE (g2:EntraGroup {id: '22222222-3333-4444-5555-666666666666', display_name: 'HR Team'})
        CREATE (t)-[:RESOURCE]->(u1)
        CREATE (t)-[:RESOURCE]->(u2)
        CREATE (t)-[:RESOURCE]->(g1)
        CREATE (t)-[:RESOURCE]->(g2)
        """,
        {"tenant_id": TEST_TENANT_ID},
    )


def _ensure_local_neo4j_has_aws_identity_center(neo4j_session):
    """
    Create AWS Identity Center instance for federation testing.
    """
    # Load AWS Identity Center instance using the existing loader
    cartography.intel.aws.identitycenter.load_identity_center_instances(
        neo4j_session,
        tests.data.aws.identitycenter.LIST_INSTANCES,
        "us-west-2",
        "123456789012",
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_aws_sso_users(neo4j_session):
    """
    Create AWS SSO users for identity federation testing.
    """
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


async def _mock_get_entra_applications(client):
    """Mock async generator for get_entra_applications"""
    for app in MOCK_ENTRA_APPLICATIONS:
        yield app


async def _mock_get_entra_service_principals(client):
    """Mock async generator for get_entra_service_principals"""
    for spn in MOCK_SERVICE_PRINCIPALS:
        yield spn


async def _mock_get_app_role_assignments_for_app(client, neo4j_session, app_id):
    """Mock async generator for get_app_role_assignments_for_app"""
    # Return assignments that match this app_id
    assignments, _ = _prepare_mock_assignments()

    # Map app_id to display names for filtering
    app_id_to_display = {
        "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee": "Finance Tracker",
        "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb": "HR Portal",
    }

    target_display_name = app_id_to_display.get(app_id)

    for assignment in assignments:
        if assignment.resource_display_name == target_display_name:
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
    cartography.intel.microsoft.entra.app_role_assignments,
    "get_app_role_assignments_for_app",
    side_effect=_mock_get_app_role_assignments_for_app,
)
@patch.object(
    cartography.intel.microsoft.entra.applications,
    "get_entra_applications",
    side_effect=_mock_get_entra_applications,
)
@patch.object(
    cartography.intel.microsoft.entra.service_principals,
    "get_entra_service_principals",
    side_effect=_mock_get_entra_service_principals,
)
@pytest.mark.asyncio
async def test_sync_entra_applications(
    mock_get_service_principals, mock_get_apps, mock_get_assignments, neo4j_session
):
    """
    Ensure that applications actually get loaded and connected to tenant,
    and both user-app and group-app relationships exist
    """
    # Arrange: Load tenant as prerequisite
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)

    # Setup test data - create users, groups, AWS Identity Center, and AWS SSO users for relationship testing
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_aws_identity_center(neo4j_session)
    _ensure_local_neo4j_has_aws_sso_users(neo4j_session)

    # Act - sync in the correct order: applications -> service principals -> app role assignments
    # First sync applications
    await sync_entra_applications(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Then sync service principals
    await sync_service_principals(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Finally sync app role assignments (this will query the graph for applications)
    await sync_app_role_assignments(
        neo4j_session,
        TEST_TENANT_ID,
        TEST_CLIENT_ID,
        TEST_CLIENT_SECRET,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    await sync_entra_federation(
        neo4j_session,
        TEST_UPDATE_TAG,
        TEST_TENANT_ID,
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

    # Assert `_ont_enabled` is projected onto EntraApplication from the
    # linked service principal (both mock SPs have account_enabled=True).
    # The projection runs inside `sync_service_principals` so it executes
    # even on a Microsoft-only sync, without the top-level ontology stage.
    assert check_nodes(
        neo4j_session, "EntraApplication", ["display_name", "_ont_enabled"]
    ) == {
        ("Finance Tracker", True),
        ("HR Portal", True),
    }

    # Simulate one app losing its service principal (e.g. the SP was deleted
    # upstream and removed by cleanup on the next sync): drop the SP and its
    # relationship, re-run only the projection, and confirm `_ont_enabled`
    # is reset to NULL on the orphan app instead of keeping the stale `True`.
    neo4j_session.run(
        """
        MATCH (sp:EntraServicePrincipal {display_name: 'HR Portal Service Principal'})
        DETACH DELETE sp
        """,
    )
    cartography.util.run_typed_analysis_job(
        ENTRA_APPLICATION_PROJECTION,
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )
    assert check_nodes(
        neo4j_session, "EntraApplication", ["display_name", "_ont_enabled"]
    ) == {
        ("Finance Tracker", True),
        ("HR Portal", None),
    }

    # Simulate a multi-tenant Entra graph. Two invariants must hold when
    # running the projection scoped to TEST_TENANT_ID:
    #
    #   (a) Foreign-tenant SPs that link to a home-tenant app via the
    #       `app_id`-only relationship matcher must not feed _ont_enabled
    #       on the home-tenant app (Finance Tracker keeps True, not False).
    #   (b) Apps owned by another tenant must not be touched at all - the
    #       projection only operates on apps in the syncing tenant, so a
    #       pre-existing `_ont_enabled` on a foreign-tenant app is preserved.
    neo4j_session.run(
        """
        MATCH (app:EntraApplication {display_name: 'Finance Tracker'})
        WITH app
        CREATE (t2:EntraTenant {id: 'other-tenant-id'})
        CREATE (sp2:EntraServicePrincipal {
            id: 'sp-foreign-finance',
            app_id: app.app_id,
            display_name: 'Foreign Finance SP',
            account_enabled: false
        })
        CREATE (foreign_app:EntraApplication {
            id: 'foreign-app-id',
            app_id: 'foreign-app-app-id',
            display_name: 'Foreign Tenant App',
            _ont_enabled: true
        })
        CREATE (foreign_sp:EntraServicePrincipal {
            id: 'sp-foreign-app',
            app_id: 'foreign-app-app-id',
            display_name: 'Foreign Tenant App SP',
            account_enabled: false
        })
        CREATE (t2)-[:RESOURCE]->(sp2)
        CREATE (t2)-[:RESOURCE]->(foreign_app)
        CREATE (t2)-[:RESOURCE]->(foreign_sp)
        CREATE (app)-[:SERVICE_PRINCIPAL]->(sp2)
        CREATE (foreign_app)-[:SERVICE_PRINCIPAL]->(foreign_sp)
        """,
    )
    cartography.util.run_typed_analysis_job(
        ENTRA_APPLICATION_PROJECTION,
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )
    assert check_nodes(
        neo4j_session, "EntraApplication", ["display_name", "_ont_enabled"]
    ) == {
        ("Finance Tracker", True),
        ("HR Portal", None),
        # Foreign-tenant app keeps its pre-existing value: the projection
        # scoped to TEST_TENANT_ID does not touch apps owned by other
        # tenants (would otherwise be False from foreign_sp.account_enabled).
        ("Foreign Tenant App", True),
    }
