from unittest.mock import patch

import requests

import cartography.intel.anthropic.users
import tests.data.anthropic.users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"


def _ensure_local_neo4j_has_test_users(neo4j_session):
    cartography.intel.anthropic.users.load_users(
        neo4j_session,
        tests.data.anthropic.users.ANTHROPIC_USERS,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.anthropic.users,
    "get",
    return_value=(TEST_ORG_ID, tests.data.anthropic.users.ANTHROPIC_USERS),
)
def test_load_anthropic_users(mock_api, neo4j_session):
    """
    Ensure that users actually get loaded
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
    }

    # Act
    cartography.intel.anthropic.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Organization exists
    assert check_nodes(neo4j_session, "AnthropicOrganization", ["id"]) == {
        (TEST_ORG_ID,)
    }

    # Assert Users exist
    expected_nodes = {
        ("user_Oov3aYewo6ZuoGh8thaiV1uNoy1aXe", "mbsimpson@simpson.corp"),
        ("user_EneequohSheesh3Ohtaefu8we2aite", "hjsimpson@simpson.corp"),
    }
    assert (
        check_nodes(neo4j_session, "AnthropicUser", ["id", "email"]) == expected_nodes
    )

    # Assert users are linked to the correct org
    expected_rels = {
        ("user_EneequohSheesh3Ohtaefu8we2aite", TEST_ORG_ID),
        ("user_Oov3aYewo6ZuoGh8thaiV1uNoy1aXe", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicUser",
            "id",
            "AnthropicOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
