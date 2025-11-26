from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.users
from cartography.intel.okta.sync_state import OktaSyncState
from tests.data.okta.users import create_test_user
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789
TEST_API_KEY = "test-api-key"


@patch.object(cartography.intel.okta.users, "_create_user_client")
@patch.object(cartography.intel.okta.users, "_get_okta_users")
def test_sync_okta_users(mock_get_users, mock_user_client, neo4j_session):
    """
    Test that Okta users are synced correctly to the graph.
    This follows the recommended pattern: mock get() functions, call sync(), verify outcomes.
    """
    # Arrange - Create test users
    test_user_1 = create_test_user()
    test_user_1.id = "user-001"
    test_user_1.profile.email = "alice@example.com"
    test_user_1.profile.login = "alice@example.com"
    test_user_1.profile.firstName = "Alice"
    test_user_1.profile.lastName = "Smith"

    test_user_2 = create_test_user()
    test_user_2.id = "user-002"
    test_user_2.profile.email = "bob@example.com"
    test_user_2.profile.login = "bob@example.com"
    test_user_2.profile.firstName = "Bob"
    test_user_2.profile.lastName = "Johnson"

    test_user_3 = create_test_user()
    test_user_3.id = "user-003"
    test_user_3.profile.email = "charlie@example.com"
    test_user_3.profile.login = "charlie@example.com"
    test_user_3.profile.firstName = "Charlie"
    test_user_3.profile.lastName = "Brown"

    # Mock the API calls
    mock_get_users.return_value = [test_user_1, test_user_2, test_user_3]
    mock_user_client.return_value = MagicMock()

    # Create the OktaOrganization node first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    sync_state = OktaSyncState()

    # Act - Call the main sync function
    cartography.intel.okta.users.sync_okta_users(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - Verify users were created with correct properties
    expected_users = {
        ("user-001", "Alice", "Smith", "alice@example.com"),
        ("user-002", "Bob", "Johnson", "bob@example.com"),
        ("user-003", "Charlie", "Brown", "charlie@example.com"),
    }
    actual_users = check_nodes(
        neo4j_session, "OktaUser", ["id", "first_name", "last_name", "email"]
    )
    assert actual_users == expected_users

    # Assert - Verify users have UserAccount label
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser:UserAccount)
        RETURN u.id as user_id
        """,
    )
    user_account_ids = {r["user_id"] for r in result}
    assert user_account_ids == {"user-001", "user-002", "user-003"}

    # Assert - Verify users are connected to organization
    expected_org_rels = {
        (TEST_ORG_ID, "user-001"),
        (TEST_ORG_ID, "user-002"),
        (TEST_ORG_ID, "user-003"),
    }
    actual_org_rels = check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaUser",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert actual_org_rels == expected_org_rels

    # Assert - Verify Human nodes were created with IDENTITY_OKTA relationships
    expected_human_rels = {
        ("alice@example.com", "user-001"),
        ("bob@example.com", "user-002"),
        ("charlie@example.com", "user-003"),
    }
    actual_human_rels = check_rels(
        neo4j_session,
        "Human",
        "email",
        "OktaUser",
        "id",
        "IDENTITY_OKTA",
        rel_direction_right=True,
    )
    assert actual_human_rels == expected_human_rels

    # Assert - Verify ontology fields are set correctly
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser{id: 'user-001'})
        RETURN u._ont_email as email, u._ont_firstname as first, u._ont_lastname as last, u._ont_source as source
        """,
    )
    ont_data = [dict(r) for r in result][0]
    assert ont_data == {
        "email": "alice@example.com",
        "first": "Alice",
        "last": "Smith",
        "source": "okta",
    }


@patch.object(cartography.intel.okta.users, "_create_user_client")
@patch.object(cartography.intel.okta.users, "_get_okta_users")
def test_sync_okta_users_with_optional_fields(
    mock_get_users, mock_user_client, neo4j_session
):
    """
    Test that users with missing optional fields are handled correctly.
    """
    # Arrange - Create a user with some optional fields missing
    test_user = create_test_user()
    test_user.id = "user-minimal"
    test_user.profile.email = "minimal@example.com"
    test_user.profile.login = "minimal@example.com"
    test_user.profile.firstName = "Minimal"
    test_user.profile.lastName = "User"
    # Set optional fields to None
    test_user.activated = None
    test_user.lastLogin = None
    test_user.passwordChanged = None
    test_user.transitioningToStatus = None

    mock_get_users.return_value = [test_user]
    mock_user_client.return_value = MagicMock()

    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    sync_state = OktaSyncState()

    # Act
    cartography.intel.okta.users.sync_okta_users(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - User should be created with null optional fields
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser{id: 'user-minimal'})
        RETURN u.activated as activated, u.last_login as last_login,
               u.password_changed as password_changed, u.transition_to_status as transition_to_status
        """,
    )
    user_data = [dict(r) for r in result][0]
    assert user_data["activated"] is None
    assert user_data["last_login"] is None
    assert user_data["password_changed"] is None
    assert user_data["transition_to_status"] is None


@patch.object(cartography.intel.okta.users, "_create_user_client")
@patch.object(cartography.intel.okta.users, "_get_okta_users")
def test_sync_okta_users_updates_existing(
    mock_get_users, mock_user_client, neo4j_session
):
    """
    Test that syncing updates existing users rather than creating duplicates.
    """
    # Arrange - Create an existing user in the graph
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u:OktaUser{id: 'user-existing'})
        SET u.first_name = 'OldFirstName',
            u.last_name = 'OldLastName',
            u.email = 'old@example.com',
            u.lastupdated = 111111
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Create updated user data
    test_user = create_test_user()
    test_user.id = "user-existing"
    test_user.profile.email = "updated@example.com"
    test_user.profile.login = "updated@example.com"
    test_user.profile.firstName = "UpdatedFirst"
    test_user.profile.lastName = "UpdatedLast"

    mock_get_users.return_value = [test_user]
    mock_user_client.return_value = MagicMock()

    sync_state = OktaSyncState()

    # Act
    cartography.intel.okta.users.sync_okta_users(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - User should be updated, not duplicated
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser{id: 'user-existing'})
        RETURN u.first_name as first_name, u.last_name as last_name,
               u.email as email, u.lastupdated as lastupdated
        """,
    )
    users = [dict(r) for r in result]
    assert len(users) == 1  # Should be only one user, not a duplicate
    user_data = users[0]
    assert user_data["first_name"] == "UpdatedFirst"
    assert user_data["last_name"] == "UpdatedLast"
    assert user_data["email"] == "updated@example.com"
    assert user_data["lastupdated"] == TEST_UPDATE_TAG


@patch.object(cartography.intel.okta.users, "_create_user_client")
@patch.object(cartography.intel.okta.users, "_get_okta_users")
def test_sync_okta_users_stores_state(mock_get_users, mock_user_client, neo4j_session):
    """
    Test that sync stores user IDs in sync_state for use by other modules.
    """
    # Arrange
    test_user_1 = create_test_user()
    test_user_1.id = "user-state-1"
    test_user_1.profile.email = "state1@example.com"

    test_user_2 = create_test_user()
    test_user_2.id = "user-state-2"
    test_user_2.profile.email = "state2@example.com"

    mock_get_users.return_value = [test_user_1, test_user_2]
    mock_user_client.return_value = MagicMock()

    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    sync_state = OktaSyncState()

    # Act
    cartography.intel.okta.users.sync_okta_users(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - sync_state should contain the user IDs
    assert sync_state.users == ["user-state-1", "user-state-2"]
