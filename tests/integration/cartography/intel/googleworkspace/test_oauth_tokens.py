from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.googleworkspace.oauth_tokens
from cartography.intel.googleworkspace.oauth_tokens import (
    sync_googleworkspace_oauth_tokens,
)
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


def _mock_get_oauth_tokens_for_user(admin, user_key):
    """Mock function that returns OAuth tokens for a user"""
    tokens = MOCK_GOOGLEWORKSPACE_OAUTH_TOKENS_BY_USER.get(user_key, [])
    # Add user_key to each token
    for token in tokens:
        token["user_key"] = user_key
    return tokens


@patch.object(
    cartography.intel.googleworkspace.oauth_tokens,
    "get_oauth_tokens_for_user",
    side_effect=_mock_get_oauth_tokens_for_user,
)
def test_sync_googleworkspace_oauth_tokens(_mock_get_oauth_tokens, neo4j_session):
    """
    Test that Google Workspace OAuth tokens sync correctly and create proper nodes and relationships
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CUSTOMER_ID": TEST_CUSTOMER_ID,
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Transform users for the sync function
    transformed_users = [
        {"primaryEmail": "mbsimpson@simpson.corp", "id": "user-1"},
        {"primaryEmail": "hjsimpson@simpson.corp", "id": "user-2"},
    ]

    # Act
    sync_googleworkspace_oauth_tokens(
        neo4j_session,
        admin=MagicMock(),  # Mocked
        users=transformed_users,
        googleworkspace_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert - Verify OAuth tokens are created
    expected_tokens = {
        (
            "123456789.apps.googleusercontent.com:mbsimpson@simpson.corp",
            "123456789.apps.googleusercontent.com",
            "Slack",
        ),
        (
            "987654321.apps.googleusercontent.com:mbsimpson@simpson.corp",
            "987654321.apps.googleusercontent.com",
            "Google Calendar Mobile",
        ),
        (
            "123456789.apps.googleusercontent.com:hjsimpson@simpson.corp",
            "123456789.apps.googleusercontent.com",
            "Slack",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GoogleWorkspaceOAuthToken",
            ["id", "client_id", "display_text"],
        )
        == expected_tokens
    )

    # Assert - Verify tokens are connected to users
    expected_token_user_rels = {
        (
            "123456789.apps.googleusercontent.com:mbsimpson@simpson.corp",
            "user-1",
        ),
        (
            "987654321.apps.googleusercontent.com:mbsimpson@simpson.corp",
            "user-1",
        ),
        (
            "123456789.apps.googleusercontent.com:hjsimpson@simpson.corp",
            "user-2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GoogleWorkspaceOAuthToken",
            "id",
            "GoogleWorkspaceUser",
            "id",
            "AUTHORIZED_BY",
            rel_direction_right=True,
        )
        == expected_token_user_rels
    )

    # Assert - Verify tokens are connected to tenant
    expected_token_tenant_rels = {
        (
            "123456789.apps.googleusercontent.com:mbsimpson@simpson.corp",
            TEST_CUSTOMER_ID,
        ),
        (
            "987654321.apps.googleusercontent.com:mbsimpson@simpson.corp",
            TEST_CUSTOMER_ID,
        ),
        (
            "123456789.apps.googleusercontent.com:hjsimpson@simpson.corp",
            TEST_CUSTOMER_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GoogleWorkspaceOAuthToken",
            "id",
            "GoogleWorkspaceTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_token_tenant_rels
    )


@patch.object(
    cartography.intel.googleworkspace.oauth_tokens,
    "get_oauth_tokens_for_user",
    side_effect=_mock_get_oauth_tokens_for_user,
)
def test_oauth_token_properties(_mock_get_oauth_tokens, neo4j_session):
    """
    Test that OAuth token properties are correctly stored
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CUSTOMER_ID": TEST_CUSTOMER_ID,
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    transformed_users = [
        {"primaryEmail": "mbsimpson@simpson.corp", "id": "user-1"},
    ]

    # Act
    sync_googleworkspace_oauth_tokens(
        neo4j_session,
        admin=MagicMock(),
        users=transformed_users,
        googleworkspace_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert - Verify token properties
    query = """
    MATCH (t:GoogleWorkspaceOAuthToken)
    WHERE t.client_id = '123456789.apps.googleusercontent.com'
        AND t.user_key = 'mbsimpson@simpson.corp'
    RETURN t.client_id as client_id,
           t.display_text as display_text,
           t.anonymous as anonymous,
           t.native_app as native_app,
           t.scopes as scopes
    """
    result = neo4j_session.run(query)
    record = result.single()

    assert record is not None
    assert record["client_id"] == "123456789.apps.googleusercontent.com"
    assert record["display_text"] == "Slack"
    assert record["anonymous"] is False
    assert record["native_app"] is False
    assert record["scopes"] == [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]
