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


def _ensure_local_neo4j_has_test_pipelines(neo4j_session):
    pipelines = cartography.intel.circleci.pipelines.transform(
        tests.data.circleci.pipelines.CIRCLECI_PIPELINES,
    )
    cartography.intel.circleci.pipelines.load_pipelines(
        neo4j_session,
        pipelines,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )


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
    )

    # Assert (repo is flattened from an object, not stored as a map)
    assert check_nodes(
        neo4j_session,
        "CircleCIPipeline",
        ["id", "name", "config_source_repo_full_name"],
    ) == {
        ("def-1", "build-and-test", "acme/web"),
    }
    assert check_rels(
        neo4j_session,
        "CircleCIPipeline",
        "id",
        "CircleCIProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("def-1", TEST_PROJECT_ID),
    }
