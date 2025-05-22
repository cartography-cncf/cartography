from unittest.mock import patch

import requests

import cartography.intel.openai.apikeys
import tests.data.openai.apikeys
import tests.data.openai.projects
from tests.integration.cartography.intel.openai.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.cartography.intel.openai.test_serviceaccounts import (
    _ensure_local_neo4j_has_sa_projects,
)
from tests.integration.cartography.intel.openai.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = tests.data.openai.projects.OPENAI_PROJECTS[0]["id"]


@patch.object(
    cartography.intel.openai.apikeys,
    "get",
    return_value=tests.data.openai.apikeys.OPENAI_APIKEYS,
)
def test_load_openai_apikeys(mock_api, neo4j_session):
    """
    Ensure that apikeys actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.openai.con/v1",
        "project_id": TEST_PROJECT_ID,
    }
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    _ensure_local_neo4j_has_sa_projects(neo4j_session)

    # Act
    cartography.intel.openai.apikeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_PROJECT_ID,
    )

    # Assert ProjectApiKeys exist
    expected_nodes = {
        (
            "key_Eek1lae1au5Iepi2eeza",
            "Homer Assistant",
        ),
        (
            "key_iegheiWieG2jupheeYin",
            "Chaos Monkey Script",
        ),
    }
    assert check_nodes(neo4j_session, "OpenAIApiKey", ["id", "name"]) == expected_nodes

    # Assert ProjectApiKeys are connected with Project
    expected_rels = {
        ("key_Eek1lae1au5Iepi2eeza", TEST_PROJECT_ID),
        ("key_iegheiWieG2jupheeYin", TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAIApiKey",
            "id",
            "OpenAIProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert ProjectApiKeys are connected with User
    expected_rels = {
        (
            "key_Eek1lae1au5Iepi2eeza",
            "user-ou3doohoeX6xie1Quiem",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAIApiKey",
            "id",
            "OpenAIUser",
            "id",
            "OWNS",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert ProjectApiKeys are connected with ServiceAccount
    expected_rels = {
        (
            "key_iegheiWieG2jupheeYin",
            "user-ohp0mahG0Aw5eevu6ain",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAIApiKey",
            "id",
            "OpenAIServiceAccount",
            "id",
            "OWNS",
            rel_direction_right=False,
        )
        == expected_rels
    )
