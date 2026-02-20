from unittest.mock import patch

import requests

import cartography.intel.openai.containers
import tests.data.openai.containers
import tests.data.openai.projects
from tests.integration.cartography.intel.openai.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = tests.data.openai.projects.OPENAI_PROJECTS[0]["id"]


def _ensure_local_neo4j_has_test_containers(neo4j_session):
    cartography.intel.openai.containers.load_containers(
        neo4j_session,
        tests.data.openai.containers.OPENAI_CONTAINERS,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.openai.containers,
    "get",
    return_value=tests.data.openai.containers.OPENAI_CONTAINERS,
)
def test_load_openai_containers(mock_api, neo4j_session):
    """
    Ensure that containers actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.openai.com/v1",
        "project_id": TEST_PROJECT_ID,
    }
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.openai.containers.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_PROJECT_ID,
    )

    # Assert Containers exist
    expected_nodes = {
        ("cntr-abc123def456", "data-processing"),
        ("cntr-ghi789jkl012", "model-serving"),
    }
    assert (
        check_nodes(neo4j_session, "OpenAIContainer", ["id", "name"])
        == expected_nodes
    )

    # Assert Containers are connected with Project
    expected_rels = {
        ("cntr-abc123def456", TEST_PROJECT_ID),
        ("cntr-ghi789jkl012", TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAIContainer",
            "id",
            "OpenAIProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
