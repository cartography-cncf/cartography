from unittest.mock import patch

import requests

import cartography.intel.circleci.project_env_vars
import tests.data.circleci.project_env_vars
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
    cartography.intel.circleci.project_env_vars,
    "get",
    return_value=tests.data.circleci.project_env_vars.CIRCLECI_PROJECT_ENV_VARS,
)
def test_load_circleci_project_env_vars(mock_api, neo4j_session):
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
    cartography.intel.circleci.project_env_vars.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_PROJECT_SLUG,
    )

    # Assert env vars exist with their masked value (real secret never exposed)
    assert check_nodes(
        neo4j_session, "CircleCIProjectEnvVar", ["id", "name", "value"]
    ) == {
        ("gh/acme/web:DATABASE_URL", "DATABASE_URL", "xxxx1234"),
        ("gh/acme/web:SENTRY_DSN", "SENTRY_DSN", "xxxxabcd"),
    }

    # Assert (Project)-[:RESOURCE]->(EnvVar)
    assert check_rels(
        neo4j_session,
        "CircleCIProjectEnvVar",
        "id",
        "CircleCIProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("gh/acme/web:DATABASE_URL", TEST_PROJECT_ID),
        ("gh/acme/web:SENTRY_DSN", TEST_PROJECT_ID),
    }
