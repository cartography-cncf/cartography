from unittest.mock import patch

import requests

import cartography.intel.openai.serviceaccounts
import tests.data.openai.projects
import tests.data.openai.serviceaccounts
from tests.integration.cartography.intel.openai.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = tests.data.openai.projects.OPENAI_PROJECTS[0]["id"]


def _ensure_local_neo4j_has_sa_projects(neo4j_session):
    cartography.intel.openai.serviceaccounts.load_serviceaccounts(
        neo4j_session,
        tests.data.openai.serviceaccounts.OPENAI_SERVICEACCOUNTS,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.openai.serviceaccounts,
    "get",
    return_value=tests.data.openai.serviceaccounts.OPENAI_SERVICEACCOUNTS,
)
def test_load_openai_serviceaccounts(mock_api, neo4j_session):
    """
    Ensure that serviceaccounts actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.openai.con/v1",
        "project_id": TEST_PROJECT_ID,
    }
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.openai.serviceaccounts.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_PROJECT_ID,
    )

    # Assert ProjectServiceAccounts exist
    expected_nodes = {
        (
            "user-ohp0mahG0Aw5eevu6ain",
            "Chaos Monker SA",
        ),
    }
    assert (
        check_nodes(neo4j_session, "OpenAIServiceAccount", ["id", "name"])
        == expected_nodes
    )

    # Assert ProjectServiceAccounts are connected with Project
    expected_rels = {("user-ohp0mahG0Aw5eevu6ain", TEST_PROJECT_ID)}
    assert (
        check_rels(
            neo4j_session,
            "OpenAIServiceAccount",
            "id",
            "OpenAIProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
