from unittest.mock import patch

import cartography.intel.googleworkspace.groups
import cartography.intel.googleworkspace.users
from cartography.intel.googleworkspace.groups import sync_googleworkspace_groups
from cartography.intel.googleworkspace.users import sync_googleworkspace_users
from tests.data.googleworkspace.api import MOCK_GOOGLEWORKSPACE_GROUPS_RESPONSE
from tests.data.googleworkspace.api import MOCK_GOOGLEWORKSPACE_MEMBERS_BY_GROUP_EMAIL
from tests.data.googleworkspace.api import MOCK_GOOGLEWORKSPACE_USERS_RESPONSE
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
COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "CUSTOMER_ID": TEST_CUSTOMER_ID,
}


def _ensure_local_neo4j_has_test_groups(neo4j_session):
    """Load test groups into Neo4j"""
    # Transform and load groups
    groups, group_member_rels, group_owner_rels = (
        cartography.intel.googleworkspace.groups.transform_groups(
            MOCK_GOOGLEWORKSPACE_GROUPS_RESPONSE,
            MOCK_GOOGLEWORKSPACE_MEMBERS_BY_GROUP_EMAIL,
        )
    )

    cartography.intel.googleworkspace.groups.load_googleworkspace_groups(
        neo4j_session,
        groups,
        TEST_CUSTOMER_ID,
        TEST_UPDATE_TAG,
    )

    # Load group-to-group relationships
    cartography.intel.googleworkspace.groups.load_googleworkspace_group_to_group_relationships(
        neo4j_session,
        group_member_rels,
        group_owner_rels,
        TEST_CUSTOMER_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.googleworkspace.groups,
    "get_members_for_groups",
    return_value=MOCK_GOOGLEWORKSPACE_MEMBERS_BY_GROUP_EMAIL,
)
@patch.object(
    cartography.intel.googleworkspace.groups,
    "get_all_groups",
    return_value=MOCK_GOOGLEWORKSPACE_GROUPS_RESPONSE,
)
def test_sync_googleworkspace_groups(
    _mock_get_all_groups,
    _mock_get_members_for_groups,
    neo4j_session,
):
    """
    Test that Google Workspace groups sync correctly and create proper nodes
    """
    # Arrange - Ensure tenant exists
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    sync_googleworkspace_groups(
        neo4j_session,
        admin=None,  # Mocked
        googleworkspace_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMETERS,
    )

    # Assert - Verify groups are created
    expected_groups = {
        ("group-engineering", "engineering@simpson.corp", "Engineering"),
        ("group-operations", "operations@simpson.corp", "Operations"),
    }
    assert (
        check_nodes(neo4j_session, "GoogleWorkspaceGroup", ["id", "email", "name"])
        == expected_groups
    )

    # TODO: Add asserts for group-to-tenant relationships

    # Assert
    expected_user_group_rels = {
        ("user-1", "group-engineering"),
        ("user-2", "group-engineering"),
        ("user-2", "group-operations"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GoogleWorkspaceUser",
            "id",
            "GoogleWorkspaceGroup",
            "id",
            "MEMBER_OF",
        )
        == expected_user_group_rels
    )


@patch.object(
    cartography.intel.googleworkspace.groups,
    "get_members_for_groups",
    return_value=MOCK_GOOGLEWORKSPACE_MEMBERS_BY_GROUP_EMAIL,
)
@patch.object(
    cartography.intel.googleworkspace.groups,
    "get_all_groups",
    return_value=MOCK_GOOGLEWORKSPACE_GROUPS_RESPONSE,
)
@patch.object(
    cartography.intel.googleworkspace.users,
    "get_all_users",
    return_value=MOCK_GOOGLEWORKSPACE_USERS_RESPONSE,
)
def test_sync_googleworkspace_groups_creates_group_hierarchy(
    _mock_get_all_users,
    _mock_get_all_groups,
    _mock_get_members_for_groups,
    neo4j_session,
):
    """
    Test that syncing groups creates proper group-to-group hierarchy relationships
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    sync_googleworkspace_users(
        neo4j_session,
        admin=None,  # Mocked
        googleworkspace_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMETERS,
    )
    sync_googleworkspace_groups(
        neo4j_session,
        admin=None,  # Mocked
        googleworkspace_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMETERS,
    )

    # Assert
    expected_group_rels = {
        ("group-operations", "group-engineering"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GoogleWorkspaceGroup",
            "id",
            "GoogleWorkspaceGroup",
            "id",
            "MEMBER_OF",
        )
        == expected_group_rels
    )
