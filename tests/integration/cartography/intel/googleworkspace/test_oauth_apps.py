from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.googleworkspace.oauth_apps
from cartography.intel.googleworkspace.oauth_apps import sync_googleworkspace_oauth_apps
from tests.data.googleworkspace.api import MOCK_GOOGLEWORKSPACE_OAUTH_TOKENS_BY_USER
from tests.integration.cartography.intel.googleworkspace.test_tenant import (
    _ensure_local_neo4j_has_test_tenant,
)
from tests.integration.cartography.intel.googleworkspace.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CUSTOMER_ID = "ABC123CD"


def _mock_get_oauth_tokens_for_user(admin, user_id):
    """Mock function that returns OAuth tokens for a user"""
    tokens = MOCK_GOOGLEWORKSPACE_OAUTH_TOKENS_BY_USER.get(user_id, [])
    # Add user_id to each token
    for token in tokens:
        token["user_id"] = user_id
    return tokens


@patch.object(
    cartography.intel.googleworkspace.oauth_apps,
    "get_oauth_tokens_for_user",
    side_effect=_mock_get_oauth_tokens_for_user,
)
def test_sync_googleworkspace_oauth_apps(_mock_get_oauth_tokens, neo4j_session):
    """
    Test that Google Workspace OAuth apps sync correctly and create proper nodes and relationships
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CUSTOMER_ID": TEST_CUSTOMER_ID,
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    user_ids = ["user-1", "user-2"]

    # Act
    sync_googleworkspace_oauth_apps(
        neo4j_session,
        admin=MagicMock(),  # Mocked
        user_ids=user_ids,
        googleworkspace_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert - Verify OAuth apps are created (unique by client_id)
    expected_apps = {
        ("123456789.apps.googleusercontent.com", "Slack"),
        ("987654321.apps.googleusercontent.com", "Google Calendar Mobile"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GoogleWorkspaceOAuthApp",
            ["client_id", "display_text"],
        )
        == expected_apps
    )

    # Assert - Verify users are authorized to apps with AUTHORIZED relationship
    # User-1 authorized 2 apps, User-2 authorized 1 app = 3 total relationships
    query = """
    MATCH (u:GoogleWorkspaceUser)-[r:AUTHORIZED]->(app:GoogleWorkspaceOAuthApp)
    RETURN u.id as user_id, app.client_id as client_id, r.scopes as scopes
    ORDER BY user_id, client_id
    """
    result = neo4j_session.run(query)
    authorizations = [
        (record["user_id"], record["client_id"], record["scopes"]) for record in result
    ]

    expected_authorizations = [
        (
            "user-1",
            "123456789.apps.googleusercontent.com",
            [
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
        ),
        (
            "user-1",
            "987654321.apps.googleusercontent.com",
            ["https://www.googleapis.com/auth/calendar"],
        ),
        (
            "user-2",
            "123456789.apps.googleusercontent.com",
            [
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
        ),
    ]

    assert authorizations == expected_authorizations

    # Assert - Verify apps are connected to tenant
    expected_app_tenant_rels = {
        ("123456789.apps.googleusercontent.com", TEST_CUSTOMER_ID),
        ("987654321.apps.googleusercontent.com", TEST_CUSTOMER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "GoogleWorkspaceOAuthApp",
            "client_id",
            "GoogleWorkspaceTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_app_tenant_rels
    )


@patch.object(
    cartography.intel.googleworkspace.oauth_apps,
    "get_oauth_tokens_for_user",
    side_effect=_mock_get_oauth_tokens_for_user,
)
def test_oauth_app_properties(_mock_get_oauth_tokens, neo4j_session):
    """
    Test that OAuth app properties are correctly stored
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CUSTOMER_ID": TEST_CUSTOMER_ID,
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    user_ids = ["user-1"]

    # Act
    sync_googleworkspace_oauth_apps(
        neo4j_session,
        admin=MagicMock(),
        user_ids=user_ids,
        googleworkspace_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert - Verify app properties
    query = """
    MATCH (app:GoogleWorkspaceOAuthApp)
    WHERE app.client_id = '123456789.apps.googleusercontent.com'
    RETURN app.client_id as client_id,
           app.display_text as display_text,
           app.anonymous as anonymous,
           app.native_app as native_app
    """
    result = neo4j_session.run(query)
    record = result.single()

    assert record is not None
    assert record["client_id"] == "123456789.apps.googleusercontent.com"
    assert record["display_text"] == "Slack"
    assert record["anonymous"] is False
    assert record["native_app"] is False


@patch.object(
    cartography.intel.googleworkspace.oauth_apps,
    "get_oauth_tokens_for_user",
    side_effect=_mock_get_oauth_tokens_for_user,
)
def test_oauth_app_deduplication(_mock_get_oauth_tokens, neo4j_session):
    """
    Test that the same OAuth app used by multiple users creates only one app node
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CUSTOMER_ID": TEST_CUSTOMER_ID,
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Both users have authorized the Slack app (client_id: 123456789.apps.googleusercontent.com)
    user_ids = ["user-1", "user-2"]

    # Act
    sync_googleworkspace_oauth_apps(
        neo4j_session,
        admin=MagicMock(),
        user_ids=user_ids,
        googleworkspace_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert - Verify only 2 unique apps exist (Slack and Calendar)
    query = """
    MATCH (app:GoogleWorkspaceOAuthApp)
    RETURN count(app) as app_count
    """
    result = neo4j_session.run(query)
    record = result.single()
    assert record["app_count"] == 2

    # Assert - Verify Slack app has 2 AUTHORIZED relationships (one from each user)
    query = """
    MATCH (u:GoogleWorkspaceUser)-[r:AUTHORIZED]->(app:GoogleWorkspaceOAuthApp {client_id: '123456789.apps.googleusercontent.com'})
    RETURN count(r) as auth_count
    """
    result = neo4j_session.run(query)
    record = result.single()
    assert record["auth_count"] == 2
