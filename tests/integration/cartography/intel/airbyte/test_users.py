from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.airbyte.users
import tests.data.airbyte.users
from tests.integration.cartography.intel.airbyte.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.cartography.intel.airbyte.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "31634962-4b3c-4b0c-810d-a2a77d6df222"


def _mock_get_permissions(api_session, user_id, org_id):
    """
    Mock function to return permissions for a user.
    """
    result = []
    for permission in tests.data.airbyte.users.AIRBYTE_USERS_PERMISSIONS:
        if permission["userId"] == user_id:
            result.append(permission)
    return result


@patch.object(
    cartography.intel.airbyte.users,
    "get_permissions",
    side_effect=_mock_get_permissions,
)
@patch.object(
    cartography.intel.airbyte.users,
    "get",
    return_value=tests.data.airbyte.users.AIRBYTE_USERS,
)
def test_load_airbyte_users(mock_api, mock_permissions, neo4j_session):
    """
    Ensure that users actually get loaded
    """

    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)

    # Act
    cartography.intel.airbyte.users.sync(
        neo4j_session,
        api_session,
        TEST_ORG_ID,
        common_job_parameters,
    )

    # Assert Users exist
    expected_nodes = {
        (
            "9507b572-7f70-4eba-94fe-baf54fdc05ae",
            "hjsimpson@simpson.corp",
        ),
        (
            "eae5cd19-72c4-49b0-87b3-e2f0c99344a3",
            "mbsimpson@simpson.corp",
        ),
    }
    assert check_nodes(neo4j_session, "AirbyteUser", ["id", "email"]) == expected_nodes

    # Assert User-Organizations relationships exist
    expected_rels = {
        ("9507b572-7f70-4eba-94fe-baf54fdc05ae", TEST_ORG_ID),
        ("eae5cd19-72c4-49b0-87b3-e2f0c99344a3", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteUser",
            "id",
            "AirbyteOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert User ADMIN_OF Organization relationships exist
    expected_rels = {
        ("eae5cd19-72c4-49b0-87b3-e2f0c99344a3", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteUser",
            "id",
            "AirbyteOrganization",
            "id",
            "ADMIN_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert User MEMBER_OF Workspace relationships exist
    expected_rels = {
        (
            "9507b572-7f70-4eba-94fe-baf54fdc05ae",
            "e4388e31-9c21-461b-9b5d-1905ca28c599",
        ),
        (
            "eae5cd19-72c4-49b0-87b3-e2f0c99344a3",
            "e4388e31-9c21-461b-9b5d-1905ca28c599",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteUser",
            "id",
            "AirbyteWorkspace",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert User ADMIN_OF Workspace relationships exist
    expected_rels = {
        (
            "9507b572-7f70-4eba-94fe-baf54fdc05ae",
            "e4388e31-9c21-461b-9b5d-1905ca28c599",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AirbyteUser",
            "id",
            "AirbyteWorkspace",
            "id",
            "ADMIN_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
