from unittest.mock import patch

import cartography.intel.googleworkspace.users
from cartography.intel.googleworkspace.users import sync_googleworkspace_users
from tests.data.googleworkspace.api import MOCK_GOOGLEWORKSPACE_USERS_RESPONSE
from tests.integration.cartography.intel.googleworkspace.test_tenant import (
    _ensure_local_neo4j_has_test_tenant,
)
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_CUSTOMER_ID = "ABC123CD"


def _ensure_local_neo4j_has_test_users(neo4j_session):
    """Load test users into Neo4j"""
    # Transform and load users
    transformed_users = cartography.intel.googleworkspace.users.transform_users(
        MOCK_GOOGLEWORKSPACE_USERS_RESPONSE
    )
    cartography.intel.googleworkspace.users.load_googleworkspace_users(
        neo4j_session,
        transformed_users,
        TEST_UPDATE_TAG,
        TEST_CUSTOMER_ID,
    )


@patch.object(
    cartography.intel.googleworkspace.users,
    "get_all_users",
    return_value=MOCK_GOOGLEWORKSPACE_USERS_RESPONSE,
)
def test_sync_googleworkspace_users(_mock_get_all_users, neo4j_session):
    """
    Test that Google Workspace users sync correctly and create proper nodes
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CUSTOMER_ID": TEST_CUSTOMER_ID,
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)

    # Act
    sync_googleworkspace_users(
        neo4j_session,
        admin=None,  # Mocked
        googleworkspace_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert - Verify users are created
    expected_users = {
        ("user-1", "mbsimpson@simpson.corp", "Marge Simpson"),
        ("user-2", "hjsimpson@simpson.corp", "Homer Simpson"),
    }
    assert (
        check_nodes(
            neo4j_session, "GoogleWorkspaceUser", ["id", "primary_email", "name"]
        )
        == expected_users
    )

    # Assert - Verify tenant was created and users are connected to it
    expected_tenant_nodes = {
        (TEST_CUSTOMER_ID,),
    }
    assert (
        check_nodes(neo4j_session, "GoogleWorkspaceTenant", ["id"])
        == expected_tenant_nodes
    )
