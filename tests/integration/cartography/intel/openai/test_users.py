from unittest.mock import patch

import requests

import cartography.intel.openai.users
import tests.data.openai.users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org-iwai3meew4phaeNgu8ae"


def _ensure_local_neo4j_has_test_users(neo4j_session):
    cartography.intel.openai.users.load_users(
        neo4j_session,
        tests.data.openai.users.OPENAI_USERS,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.openai.users,
    "get",
    return_value=tests.data.openai.users.OPENAI_USERS,
)
def test_load_openai_users(mock_api, neo4j_session):
    """
    Ensure that users actually get loaded
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.openai.com/v1",
        "ORG_ID": TEST_ORG_ID,
    }

    # Act
    cartography.intel.openai.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG_ID,
    )

    # Assert Organization exists
    assert check_nodes(neo4j_session, "OpenAIOrganization", ["id"]) == {(TEST_ORG_ID,)}

    # Assert Users exist
    expected_nodes = {
        (
            "user-ou3doohoeX6xie1Quiem",
            "hjsimpson@simpson.corp",
        ),
        (
            "user-uJeighaeFair8shaa2av",
            "mbsimpson@simpson.corp",
        ),
    }
    assert check_nodes(neo4j_session, "OpenAIUser", ["id", "email"]) == expected_nodes

    # Assert users are linked to the correct org
    expected_rels = {
        (
            "user-ou3doohoeX6xie1Quiem",
            TEST_ORG_ID,
        ),
        (
            "user-uJeighaeFair8shaa2av",
            TEST_ORG_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAIUser",
            "id",
            "OpenAIOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
