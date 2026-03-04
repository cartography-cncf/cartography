from unittest.mock import patch

import requests

import cartography.intel.openai.vectorstores
import tests.data.openai.projects
import tests.data.openai.vectorstores
from tests.integration.cartography.intel.openai.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = tests.data.openai.projects.OPENAI_PROJECTS[0]["id"]


def _ensure_local_neo4j_has_test_vectorstores(neo4j_session):
    cartography.intel.openai.vectorstores.load_vectorstores(
        neo4j_session,
        tests.data.openai.vectorstores.OPENAI_VECTORSTORES,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.openai.vectorstores,
    "get",
    return_value=tests.data.openai.vectorstores.OPENAI_VECTORSTORES,
)
def test_load_openai_vectorstores(mock_api, neo4j_session):
    """
    Ensure that vector stores actually get loaded
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
    cartography.intel.openai.vectorstores.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_PROJECT_ID,
    )

    # Assert VectorStores exist
    expected_nodes = {
        ("vs_abc123def456", "knowledge-base"),
        ("vs_ghi789jkl012", "document-index"),
    }
    assert (
        check_nodes(neo4j_session, "OpenAIVectorStore", ["id", "name"])
        == expected_nodes
    )

    # Assert VectorStores are connected with Project
    expected_rels = {
        ("vs_abc123def456", TEST_PROJECT_ID),
        ("vs_ghi789jkl012", TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAIVectorStore",
            "id",
            "OpenAIProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
