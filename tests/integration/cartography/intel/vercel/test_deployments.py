import copy
from unittest.mock import patch

import requests

import cartography.intel.vercel.deployments
import tests.data.vercel.deployments
from tests.integration.cartography.intel.vercel.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.cartography.intel.vercel.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"
TEST_PROJECT_ID = "prj_abc"


def _ensure_local_neo4j_has_test_deployments(neo4j_session):
    deployments = copy.deepcopy(tests.data.vercel.deployments.VERCEL_DEPLOYMENTS)
    cartography.intel.vercel.deployments.transform(deployments)
    cartography.intel.vercel.deployments.load_deployments(
        neo4j_session,
        deployments,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.deployments,
    "get",
    return_value=copy.deepcopy(tests.data.vercel.deployments.VERCEL_DEPLOYMENTS),
)
def test_load_vercel_deployments(mock_api, neo4j_session):
    """
    Ensure that deployments actually get loaded and linked to their project and creator
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
        "project_id": TEST_PROJECT_ID,
    }
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.vercel.deployments.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        project_id=TEST_PROJECT_ID,
    )

    # Assert Deployments exist
    expected_nodes = {
        ("dpl_123",),
        ("dpl_456",),
    }
    assert check_nodes(neo4j_session, "VercelDeployment", ["id"]) == expected_nodes

    # Assert Deployments are connected to Project via RESOURCE (Project -RESOURCE-> Deployment)
    expected_project_rels = {
        ("dpl_123", TEST_PROJECT_ID),
        ("dpl_456", TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelDeployment",
            "id",
            "VercelProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_project_rels
    )

    # Assert Deployments are connected to creator User via CREATED_BY
    expected_user_rels = {
        ("dpl_123", "user_homer"),
        ("dpl_456", "user_homer"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelDeployment",
            "id",
            "VercelUser",
            "id",
            "CREATED_BY",
            rel_direction_right=True,
        )
        == expected_user_rels
    )
