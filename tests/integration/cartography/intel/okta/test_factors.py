from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.factors
from cartography.intel.okta.sync_state import OktaSyncState
from tests.data.okta.userfactors import create_test_factor
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789
TEST_API_KEY = "test-api-key"


@patch.object(cartography.intel.okta.factors, "_create_factor_client")
@patch.object(cartography.intel.okta.factors, "_get_factor_for_user_id")
def test_sync_users_factors(mock_get_factors, mock_factor_client, neo4j_session):
    """
    Test that Okta user factors are synced correctly to the graph.
    This follows the recommended pattern: mock get() functions, call sync(), verify outcomes.
    """
    # Arrange - Create test users in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u1:OktaUser{id: 'user-001', email: 'user1@example.com'})
        SET u1.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u2:OktaUser{id: 'user-002', email: 'user2@example.com'})
        SET u2.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Create test factors for user-001
    factor_totp = create_test_factor()
    factor_totp.id = "factor-totp-001"
    factor_totp.factorType = "token:software:totp"
    factor_totp.provider = "GOOGLE"
    factor_totp.status = "ACTIVE"

    factor_sms = create_test_factor()
    factor_sms.id = "factor-sms-001"
    factor_sms.factorType = "sms"
    factor_sms.provider = "OKTA"
    factor_sms.status = "ACTIVE"

    # Create test factors for user-002
    factor_push = create_test_factor()
    factor_push.id = "factor-push-002"
    factor_push.factorType = "push"
    factor_push.provider = "OKTA"
    factor_push.status = "ACTIVE"

    # Mock the API calls - return different factors for different users
    def mock_get_factors_side_effect(factor_client, user_id):
        if user_id == "user-001":
            return [factor_totp, factor_sms]
        elif user_id == "user-002":
            return [factor_push]
        return []

    mock_get_factors.side_effect = mock_get_factors_side_effect
    mock_factor_client.return_value = MagicMock()

    # Setup sync state with user IDs
    sync_state = OktaSyncState()
    sync_state.users = ["user-001", "user-002"]

    # Act - Call the main sync function
    cartography.intel.okta.factors.sync_users_factors(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - Verify factors were created with correct properties
    expected_factors = {
        ("factor-totp-001", "token:software:totp", "GOOGLE"),
        ("factor-sms-001", "sms", "OKTA"),
        ("factor-push-002", "push", "OKTA"),
    }
    actual_factors = check_nodes(
        neo4j_session, "OktaUserFactor", ["id", "factor_type", "provider"]
    )
    assert actual_factors == expected_factors

    # Assert - Verify FACTOR relationships between users and factors
    expected_user_factor_rels = {
        ("user-001", "factor-totp-001"),
        ("user-001", "factor-sms-001"),
        ("user-002", "factor-push-002"),
    }
    actual_user_factor_rels = check_rels(
        neo4j_session,
        "OktaUser",
        "id",
        "OktaUserFactor",
        "id",
        "FACTOR",
        rel_direction_right=True,
    )
    assert actual_user_factor_rels == expected_user_factor_rels


@patch.object(cartography.intel.okta.factors, "_create_factor_client")
@patch.object(cartography.intel.okta.factors, "_get_factor_for_user_id")
def test_sync_users_factors_with_no_users(
    mock_get_factors, mock_factor_client, neo4j_session
):
    """
    Test that sync handles gracefully when there are no users in sync_state.
    Uses a different organization ID to avoid interference from other tests.
    """
    # Arrange - Use a different org ID for isolation
    test_org_id = "test-okta-org-id-no-users"
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=test_org_id,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    mock_factor_client.return_value = MagicMock()

    # Setup sync state with empty list (not None, as None would be falsy but empty list is also handled)
    sync_state = OktaSyncState()
    sync_state.users = []  # Empty list instead of None

    # Act - Should not crash even with no users
    cartography.intel.okta.factors.sync_users_factors(
        neo4j_session,
        test_org_id,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - No factors should be created for this organization
    result = neo4j_session.run(
        """
        MATCH (org:OktaOrganization{id: $ORG_ID})-[:RESOURCE]->(u:OktaUser)-[:FACTOR]->(f:OktaUserFactor)
        RETURN count(f) as count
        """,
        ORG_ID=test_org_id,
    )
    count = [dict(r) for r in result][0]["count"]
    assert count == 0

    # Verify that _get_factor_for_user_id was never called since list is empty
    mock_get_factors.assert_not_called()


@patch.object(cartography.intel.okta.factors, "_create_factor_client")
@patch.object(cartography.intel.okta.factors, "_get_factor_for_user_id")
def test_sync_users_factors_handles_user_with_no_factors(
    mock_get_factors,
    mock_factor_client,
    neo4j_session,
):
    """
    Test that sync handles users who have no factors enrolled.
    """
    # Arrange - Create a user with no factors
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u:OktaUser{id: 'user-no-factors', email: 'nofactors@example.com'})
        SET u.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock API to return empty list for this user
    mock_get_factors.return_value = []
    mock_factor_client.return_value = MagicMock()

    sync_state = OktaSyncState()
    sync_state.users = ["user-no-factors"]

    # Act
    cartography.intel.okta.factors.sync_users_factors(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - User should still exist but have no factors
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser{id: 'user-no-factors'})
        OPTIONAL MATCH (u)-[:FACTOR]->(f:OktaUserFactor)
        RETURN u.id as user_id, count(f) as factor_count
        """,
    )
    data = [dict(r) for r in result][0]
    assert data["user_id"] == "user-no-factors"
    assert data["factor_count"] == 0


@patch.object(cartography.intel.okta.factors, "_create_factor_client")
@patch.object(cartography.intel.okta.factors, "_get_factor_for_user_id")
def test_sync_users_factors_updates_existing(
    mock_get_factors, mock_factor_client, neo4j_session
):
    """
    Test that syncing updates existing factors rather than creating duplicates.
    """
    # Arrange - Create user with existing factor
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u:OktaUser{id: 'user-update', email: 'update@example.com'})
        SET u.lastupdated = $UPDATE_TAG
        MERGE (u)-[:FACTOR]->(f:OktaUserFactor{id: 'factor-existing'})
        SET f.status = 'PENDING_ACTIVATION',
            f.factor_type = 'sms',
            f.provider = 'OKTA',
            f.lastupdated = 111111
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Create updated factor data
    updated_factor = create_test_factor()
    updated_factor.id = "factor-existing"
    updated_factor.factorType = "sms"
    updated_factor.provider = "OKTA"
    updated_factor.status = "ACTIVE"  # Status changed from PENDING_ACTIVATION to ACTIVE

    mock_get_factors.return_value = [updated_factor]
    mock_factor_client.return_value = MagicMock()

    sync_state = OktaSyncState()
    sync_state.users = ["user-update"]

    # Act
    cartography.intel.okta.factors.sync_users_factors(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - Factor should be updated, not duplicated
    result = neo4j_session.run(
        """
        MATCH (f:OktaUserFactor{id: 'factor-existing'})
        RETURN f.status as status, f.lastupdated as lastupdated
        """,
    )
    factors = [dict(r) for r in result]
    assert len(factors) == 1  # Should be only one factor
    factor_data = factors[0]
    assert factor_data["status"] == "ACTIVE"
    assert factor_data["lastupdated"] == TEST_UPDATE_TAG


@patch.object(cartography.intel.okta.factors, "_create_factor_client")
@patch.object(cartography.intel.okta.factors, "_get_factor_for_user_id")
def test_sync_users_factors_multiple_factor_types(
    mock_get_factors,
    mock_factor_client,
    neo4j_session,
):
    """
    Test syncing various factor types (TOTP, SMS, Push, WebAuthn, etc.).
    """
    # Arrange
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u:OktaUser{id: 'user-multifactor', email: 'multi@example.com'})
        SET u.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # TODO: Get real examples of different Okta factor types from API
    # Create various factor types
    factors = []

    factor_totp = create_test_factor()
    factor_totp.id = "factor-totp"
    factor_totp.factorType = "token:software:totp"
    factor_totp.provider = "GOOGLE"
    factor_totp.status = "ACTIVE"
    factors.append(factor_totp)

    factor_sms = create_test_factor()
    factor_sms.id = "factor-sms"
    factor_sms.factorType = "sms"
    factor_sms.provider = "OKTA"
    factor_sms.status = "ACTIVE"
    factors.append(factor_sms)

    factor_push = create_test_factor()
    factor_push.id = "factor-push"
    factor_push.factorType = "push"
    factor_push.provider = "OKTA"
    factor_push.status = "ACTIVE"
    factors.append(factor_push)

    factor_webauthn = create_test_factor()
    factor_webauthn.id = "factor-webauthn"
    factor_webauthn.factorType = "webauthn"
    factor_webauthn.provider = "FIDO"
    factor_webauthn.status = "ACTIVE"
    factors.append(factor_webauthn)

    mock_get_factors.return_value = factors
    mock_factor_client.return_value = MagicMock()

    sync_state = OktaSyncState()
    sync_state.users = ["user-multifactor"]

    # Act
    cartography.intel.okta.factors.sync_users_factors(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
        sync_state,
    )

    # Assert - All factor types should be created
    result = neo4j_session.run(
        """
        MATCH (u:OktaUser{id: 'user-multifactor'})-[:FACTOR]->(f:OktaUserFactor)
        RETURN f.factor_type as factor_type
        ORDER BY f.factor_type
        """,
    )
    factor_types = [r["factor_type"] for r in result]
    assert factor_types == ["push", "sms", "token:software:totp", "webauthn"]
