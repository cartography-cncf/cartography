from unittest.mock import patch

import requests

import cartography.intel.openai.skills
import tests.data.openai.projects
import tests.data.openai.skills
from tests.integration.cartography.intel.openai.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = tests.data.openai.projects.OPENAI_PROJECTS[0]["id"]


def _ensure_local_neo4j_has_test_skills(neo4j_session):
    cartography.intel.openai.skills.load_skills(
        neo4j_session,
        tests.data.openai.skills.OPENAI_SKILLS,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.openai.skills,
    "get",
    return_value=tests.data.openai.skills.OPENAI_SKILLS,
)
def test_load_openai_skills(mock_api, neo4j_session):
    """
    Ensure that skills actually get loaded
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
    cartography.intel.openai.skills.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_PROJECT_ID,
    )

    # Assert Skills exist
    expected_nodes = {
        ("skill-abc123def456", "code-reviewer"),
        ("skill-ghi789jkl012", "data-analyzer"),
    }
    assert (
        check_nodes(neo4j_session, "OpenAISkill", ["id", "name"])
        == expected_nodes
    )

    # Assert Skills are connected with Project
    expected_rels = {
        ("skill-abc123def456", TEST_PROJECT_ID),
        ("skill-ghi789jkl012", TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAISkill",
            "id",
            "OpenAIProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
