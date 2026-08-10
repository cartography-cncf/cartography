from unittest.mock import patch

import requests

import cartography.intel.circleci.oidc
import tests.data.circleci.project_oidc
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
TEST_ORG_ID = "org-1111-aaaa"
TEST_PROJECT_ID = "proj-1"


@patch.object(
    cartography.intel.circleci.oidc,
    "get_project",
    return_value=tests.data.circleci.project_oidc.CIRCLECI_PROJECT_OIDC_CLAIMS,
)
def test_load_circleci_project_oidc(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_ID": TEST_ORG_ID,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.circleci.oidc.sync_project(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG_ID,
        TEST_PROJECT_ID,
    )

    # Assert
    assert check_nodes(neo4j_session, "CircleCIProjectOidcConfig", ["id", "scope"]) == {
        (TEST_PROJECT_ID, "project"),
    }
    assert check_rels(
        neo4j_session,
        "CircleCIProjectOidcConfig",
        "id",
        "CircleCIProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_PROJECT_ID, TEST_PROJECT_ID),
    }
