from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.roles
from cartography.intel.okta.sync_state import OktaSyncState
from tests.data.okta.adminroles import LIST_ASSIGNED_GROUP_ROLE_RESPONSE
from tests.data.okta.adminroles import LIST_ASSIGNED_USER_ROLE_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789
TEST_API_KEY = "test-api-key"


@patch.object(cartography.intel.okta.roles, "create_api_client")
@patch.object(cartography.intel.okta.roles, "_get_user_roles")
@patch.object(cartography.intel.okta.roles, "_get_group_roles")
def test_sync_roles_for_users(
    mock_get_group_roles, mock_get_user_roles, mock_api_client, neo4j_session
):
    """
    Test that Okta user admin roles are synced correctly to the graph.
    This follows the recommended pattern: mock get() functions, call sync(), verify outcomes.
    """
    # Arrange - Create organization and users in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u1:OktaUser{id: 'user-admin-001', email: 'admin1@example.com'})
        SET u1.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u2:OktaUser{id: 'user-admin-002', email: 'admin2@example.com'})
        SET u2.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    mock_get_user_roles.return_value = LIST_ASSIGNED_USER_ROLE_RESPONSE
    mock_get_group_roles.return_value = "[]"  # No group roles
    mock_api_client.return_value = MagicMock()

    # Setup sync state with user IDs
    sync_state = OktaSyncState()
    sync_state.users = ["user-admin-001", "user-admin-002"]
    sync_state.groups = []

    # Act - Call the main sync function
    cartography.intel.okta.roles.sync_roles(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - Verify admin role nodes were created
    expected_roles = {
        ("APP_ADMIN", "Application Administrator"),
        ("HELP_DESK_ADMIN", "Help Desk Administrator"),
    }
    actual_roles = check_nodes(
        neo4j_session, "OktaAdministrationRole", ["type", "label"]
    )
    assert actual_roles == expected_roles

    # Assert - Verify MEMBER_OF_OKTA_ROLE relationships between users and roles
    # Both users should have both roles since mock returns same data
    expected_user_role_rels = {
        ("user-admin-001", "APP_ADMIN"),
        ("user-admin-001", "HELP_DESK_ADMIN"),
        ("user-admin-002", "APP_ADMIN"),
        ("user-admin-002", "HELP_DESK_ADMIN"),
    }
    actual_user_role_rels = check_rels(
        neo4j_session,
        "OktaUser",
        "id",
        "OktaAdministrationRole",
        "type",
        "MEMBER_OF_OKTA_ROLE",
        rel_direction_right=True,
    )
    assert actual_user_role_rels == expected_user_role_rels

    # Assert - Verify organization has RESOURCE relationships to roles
    expected_org_role_rels = {
        (TEST_ORG_ID, "APP_ADMIN"),
        (TEST_ORG_ID, "HELP_DESK_ADMIN"),
    }
    actual_org_role_rels = check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaAdministrationRole",
        "type",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert actual_org_role_rels == expected_org_role_rels


@patch.object(cartography.intel.okta.roles, "create_api_client")
@patch.object(cartography.intel.okta.roles, "_get_user_roles")
@patch.object(cartography.intel.okta.roles, "_get_group_roles")
def test_sync_roles_for_groups(
    mock_get_group_roles, mock_get_user_roles, mock_api_client, neo4j_session
):
    """
    Test that Okta group admin roles are synced correctly to the graph.
    """
    # Arrange - Create organization and groups in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g1:OktaGroup{id: 'group-admin-001', name: 'Admins'})
        SET g1.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g2:OktaGroup{id: 'group-admin-002', name: 'Support'})
        SET g2.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    mock_get_user_roles.return_value = "[]"  # No user roles
    mock_get_group_roles.return_value = LIST_ASSIGNED_GROUP_ROLE_RESPONSE
    mock_api_client.return_value = MagicMock()

    # Setup sync state with group IDs
    sync_state = OktaSyncState()
    sync_state.users = []
    sync_state.groups = ["group-admin-001", "group-admin-002"]

    # Act
    cartography.intel.okta.roles.sync_roles(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - Verify MEMBER_OF_OKTA_ROLE relationships between groups and roles
    expected_group_role_rels = {
        ("group-admin-001", "APP_ADMIN"),
        ("group-admin-001", "HELP_DESK_ADMIN"),
        ("group-admin-002", "APP_ADMIN"),
        ("group-admin-002", "HELP_DESK_ADMIN"),
    }
    actual_group_role_rels = check_rels(
        neo4j_session,
        "OktaGroup",
        "id",
        "OktaAdministrationRole",
        "type",
        "MEMBER_OF_OKTA_ROLE",
        rel_direction_right=True,
    )
    assert actual_group_role_rels == expected_group_role_rels


@patch.object(cartography.intel.okta.roles, "create_api_client")
@patch.object(cartography.intel.okta.roles, "_get_user_roles")
@patch.object(cartography.intel.okta.roles, "_get_group_roles")
def test_sync_roles_for_users_and_groups(
    mock_get_group_roles,
    mock_get_user_roles,
    mock_api_client,
    neo4j_session,
):
    """
    Test that roles are synced for both users and groups in the same run.
    """
    # Arrange - Create organization, users, and groups
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u:OktaUser{id: 'user-mixed', email: 'mixed@example.com'})
        SET u.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g:OktaGroup{id: 'group-mixed', name: 'Mixed'})
        SET g.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    mock_get_user_roles.return_value = LIST_ASSIGNED_USER_ROLE_RESPONSE
    mock_get_group_roles.return_value = LIST_ASSIGNED_GROUP_ROLE_RESPONSE
    mock_api_client.return_value = MagicMock()

    sync_state = OktaSyncState()
    sync_state.users = ["user-mixed"]
    sync_state.groups = ["group-mixed"]

    # Act
    cartography.intel.okta.roles.sync_roles(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - Both user and group should have role relationships
    result = neo4j_session.run(
        """
        MATCH (entity)-[:MEMBER_OF_OKTA_ROLE]->(role:OktaAdministrationRole)
        WHERE entity.id IN ['user-mixed', 'group-mixed']
        RETURN entity.id as entity_id, role.type as role_type
        ORDER BY entity_id, role_type
        """,
    )
    rels = [(r["entity_id"], r["role_type"]) for r in result]
    expected = [
        ("group-mixed", "APP_ADMIN"),
        ("group-mixed", "HELP_DESK_ADMIN"),
        ("user-mixed", "APP_ADMIN"),
        ("user-mixed", "HELP_DESK_ADMIN"),
    ]
    assert rels == expected


@patch.object(cartography.intel.okta.roles, "create_api_client")
@patch.object(cartography.intel.okta.roles, "_get_user_roles")
@patch.object(cartography.intel.okta.roles, "_get_group_roles")
def test_sync_roles_handles_empty_state(
    mock_get_group_roles,
    mock_get_user_roles,
    mock_api_client,
    neo4j_session,
):
    """
    Test that sync handles gracefully when sync_state has no users or groups.
    Uses a different organization ID to avoid interference from other tests.
    """
    # Arrange - Use a different org ID for isolation
    test_org_id = "test-okta-org-id-empty-state"
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=test_org_id,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    mock_api_client.return_value = MagicMock()

    sync_state = OktaSyncState()
    sync_state.users = []  # Empty list instead of None
    sync_state.groups = []  # Empty list instead of None

    # Act - Should not crash
    cartography.intel.okta.roles.sync_roles(
        neo4j_session,
        test_org_id,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - No roles should be created for this organization
    result = neo4j_session.run(
        """
        MATCH (org:OktaOrganization{id: $ORG_ID})-[:RESOURCE]->(r:OktaAdministrationRole)
        RETURN count(r) as count
        """,
        ORG_ID=test_org_id,
    )
    count = [dict(r) for r in result][0]["count"]
    assert count == 0

    # Verify that the API methods were never called since lists are empty
    mock_get_user_roles.assert_not_called()
    mock_get_group_roles.assert_not_called()


@patch.object(cartography.intel.okta.roles, "create_api_client")
@patch.object(cartography.intel.okta.roles, "_get_user_roles")
@patch.object(cartography.intel.okta.roles, "_get_group_roles")
def test_sync_roles_handles_users_with_no_roles(
    mock_get_group_roles,
    mock_get_user_roles,
    mock_api_client,
    neo4j_session,
):
    """
    Test that sync handles users who have no admin roles.
    """
    # Arrange
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u:OktaUser{id: 'user-noroles', email: 'noroles@example.com'})
        SET u.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock API to return empty roles
    mock_get_user_roles.return_value = "[]"
    mock_get_group_roles.return_value = "[]"
    mock_api_client.return_value = MagicMock()

    sync_state = OktaSyncState()
    sync_state.users = ["user-noroles"]
    sync_state.groups = []

    # Act
    cartography.intel.okta.roles.sync_roles(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - User should exist but have no role relationships
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser{id: 'user-noroles'})
        OPTIONAL MATCH (u)-[:MEMBER_OF_OKTA_ROLE]->(r:OktaAdministrationRole)
        RETURN u.id as user_id, count(r) as role_count
        """,
    )
    data = [dict(r) for r in result][0]
    assert data["user_id"] == "user-noroles"
    assert data["role_count"] == 0


@patch.object(cartography.intel.okta.roles, "create_api_client")
@patch.object(cartography.intel.okta.roles, "_get_user_roles")
@patch.object(cartography.intel.okta.roles, "_get_group_roles")
def test_sync_roles_updates_existing(
    mock_get_group_roles,
    mock_get_user_roles,
    mock_api_client,
    neo4j_session,
):
    """
    Test that syncing updates existing role assignments.
    """
    # Arrange - Create user with existing role
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u:OktaUser{id: 'user-update-role', email: 'update@example.com'})
        SET u.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(r:OktaAdministrationRole{id: 'APP_ADMIN', type: 'APP_ADMIN'})
        SET r.label = 'Old Label', r.lastupdated = 111111
        MERGE (u)-[rel:MEMBER_OF_OKTA_ROLE]->(r)
        SET rel.lastupdated = 111111
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock API with updated data
    mock_get_user_roles.return_value = LIST_ASSIGNED_USER_ROLE_RESPONSE
    mock_get_group_roles.return_value = "[]"
    mock_api_client.return_value = MagicMock()

    sync_state = OktaSyncState()
    sync_state.users = ["user-update-role"]
    sync_state.groups = []

    # Act
    cartography.intel.okta.roles.sync_roles(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - Role should be updated with new label and update tag
    result = neo4j_session.run(
        """
        MATCH (r:OktaAdministrationRole{type: 'APP_ADMIN'})
        RETURN r.label as label, r.lastupdated as lastupdated
        """,
    )
    role_data = [dict(r) for r in result][0]
    assert role_data["label"] == "Application Administrator"  # Updated from "Old Label"
    assert role_data["lastupdated"] == TEST_UPDATE_TAG

    # Assert - Relationship should be updated
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser{id: 'user-update-role'})-[rel:MEMBER_OF_OKTA_ROLE]->(r:OktaAdministrationRole{type: 'APP_ADMIN'})
        RETURN rel.lastupdated as rel_lastupdated
        """,
    )
    rel_data = [dict(r) for r in result][0]
    assert rel_data["rel_lastupdated"] == TEST_UPDATE_TAG
