from unittest.mock import patch

import requests

import cartography.intel.anthropic.workspaces
import tests.data.anthropic.workspaces
from tests.integration.cartography.intel.anthropic.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"


def _ensure_local_neo4j_has_test_workspaces(neo4j_session):
    cartography.intel.anthropic.workspaces.load_workspaces(
        neo4j_session,
        tests.data.anthropic.workspaces.ANTHROPIC_WORKSPACES,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.anthropic.workspaces,
    "get_workspace_users",
    return_value=tests.data.anthropic.workspaces.ANTHROPIC_WORKSPACES_MEMBERS,
)
@patch.object(
    cartography.intel.anthropic.workspaces,
    "get",
    return_value=(TEST_ORG_ID, tests.data.anthropic.workspaces.ANTHROPIC_WORKSPACES),
)
def test_load_anthropic_workspaces(mock_api, mock_api_members, neo4j_session):
    """
    Ensure that workspaces actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
    }
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.anthropic.workspaces.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Workspaces exist
    expected_nodes = {
        (
            "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ",
            "Springfield Nuclear Power Plant",
        ),
    }
    assert (
        check_nodes(neo4j_session, "AnthropicWorkspace", ["id", "name"])
        == expected_nodes
    )

    # Assert workspaces are linked to the correct org
    expected_rels = {
        ("wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicWorkspace",
            "id",
            "AnthropicOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert workspaces are linked to the correct users
    expected_rels = {
        ("user_EneequohSheesh3Ohtaefu8we2aite", "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ"),
        ("user_Oov3aYewo6ZuoGh8thaiV1uNoy1aXe", "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicUser",
            "id",
            "AnthropicWorkspace",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
    expected_rels = {
        ("user_EneequohSheesh3Ohtaefu8we2aite", "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ")
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicUser",
            "id",
            "AnthropicWorkspace",
            "id",
            "ADMIN_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
