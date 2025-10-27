from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gsuite import api
from tests.data.gsuite.api import MOCK_GSUITE_GROUPS_RESPONSE
from tests.data.gsuite.api import MOCK_GSUITE_MEMBERS_BY_GROUP_EMAIL
from tests.data.gsuite.api import MOCK_GSUITE_USERS_RESPONSE
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "LIMIT_SIZE": 1000,
}


def _members_for_email(_: MagicMock, group_email: str):
    return MOCK_GSUITE_MEMBERS_BY_GROUP_EMAIL.get(group_email, [])


@patch.object(api, "get_members_for_group", side_effect=_members_for_email)
@patch.object(api, "get_all_groups", return_value=MOCK_GSUITE_GROUPS_RESPONSE)
@patch.object(api, "get_all_users", return_value=MOCK_GSUITE_USERS_RESPONSE)
def test_sync_gsuite_users_creates_user_group_memberships(
    mock_get_all_users,
    mock_get_all_groups,
    mock_get_members_for_group,
    neo4j_session,
):
    # Arrange
    admin_resource = MagicMock()

    # Act
    api.sync_gsuite_users(
        neo4j_session,
        admin_resource,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )
    api.sync_gsuite_groups(
        neo4j_session,
        admin_resource,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    # Assert
    expected_user_group_rels = {
        ("user-1", "group-engineering"),
        ("user-2", "group-engineering"),
        ("user-2", "group-operations"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GSuiteUser",
            "id",
            "GSuiteGroup",
            "id",
            "MEMBER_GSUITE_GROUP",
        )
        == expected_user_group_rels
    )


@patch.object(api, "get_members_for_group", side_effect=_members_for_email)
@patch.object(api, "get_all_groups", return_value=MOCK_GSUITE_GROUPS_RESPONSE)
@patch.object(api, "get_all_users", return_value=MOCK_GSUITE_USERS_RESPONSE)
def test_sync_gsuite_groups_creates_group_hierarchy(
    mock_get_all_users,
    mock_get_all_groups,
    mock_get_members_for_group,
    neo4j_session,
):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    admin_resource = MagicMock()

    # Act
    api.sync_gsuite_users(
        neo4j_session,
        admin_resource,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )
    api.sync_gsuite_groups(
        neo4j_session,
        admin_resource,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    # Assert
    expected_group_rels = {
        ("group-operations", "group-engineering"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GSuiteGroup",
            "id",
            "GSuiteGroup",
            "id",
            "MEMBER_GSUITE_GROUP",
        )
        == expected_group_rels
    )
