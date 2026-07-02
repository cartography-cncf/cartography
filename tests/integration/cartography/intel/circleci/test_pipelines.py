from unittest.mock import patch

import requests

import cartography.intel.circleci.pipelines
import tests.data.circleci.pipelines
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.cartography.intel.circleci.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_PROJECT_ID = "proj-1"
TEST_PROJECT_SLUG = "gh/acme/web"


@patch.object(
    cartography.intel.circleci.pipelines,
    "get",
    return_value=tests.data.circleci.pipelines.CIRCLECI_PIPELINES,
)
def test_load_circleci_pipelines(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.circleci.pipelines.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_PROJECT_SLUG,
    )

    # Assert pipelines exist
    assert check_nodes(neo4j_session, "CircleCIPipeline", ["id", "state"]) == {
        ("pipe-1", "created"),
    }

    # Assert (Project)-[:RESOURCE]->(Pipeline)
    assert check_rels(
        neo4j_session,
        "CircleCIPipeline",
        "id",
        "CircleCIProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("pipe-1", TEST_PROJECT_ID),
    }
