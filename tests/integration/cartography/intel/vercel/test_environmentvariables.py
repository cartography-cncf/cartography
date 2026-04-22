from unittest.mock import patch

import requests

import cartography.intel.vercel.edgeconfigs
import cartography.intel.vercel.environmentvariables
import tests.data.vercel.edgeconfigs
import tests.data.vercel.environmentvariables
from tests.integration.cartography.intel.vercel.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"
TEST_PROJECT_ID = "prj_abc"


def _ensure_local_neo4j_has_test_edge_configs(neo4j_session):
    cartography.intel.vercel.edgeconfigs.load_edge_configs(
        neo4j_session,
        tests.data.vercel.edgeconfigs.VERCEL_EDGE_CONFIGS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_environment_variables(neo4j_session):
    cartography.intel.vercel.environmentvariables.load_environment_variables(
        neo4j_session,
        tests.data.vercel.environmentvariables.VERCEL_ENVIRONMENT_VARIABLES,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.environmentvariables,
    "get",
    return_value=tests.data.vercel.environmentvariables.VERCEL_ENVIRONMENT_VARIABLES,
)
def test_load_vercel_environment_variables(mock_api, neo4j_session):
    """
    Ensure that environment variables actually get loaded and linked to their
    project, and to referenced edge configs when applicable
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
    _ensure_local_neo4j_has_test_projects(neo4j_session)
    _ensure_local_neo4j_has_test_edge_configs(neo4j_session)

    # Act
    cartography.intel.vercel.environmentvariables.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        project_id=TEST_PROJECT_ID,
    )

    # Assert Environment Variables exist
    expected_nodes = {
        ("env_123",),
        ("env_456",),
    }
    assert (
        check_nodes(neo4j_session, "VercelEnvironmentVariable", ["id"])
        == expected_nodes
    )

    # Assert Env Vars are connected to Project via RESOURCE
    expected_project_rels = {
        ("env_123", TEST_PROJECT_ID),
        ("env_456", TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelEnvironmentVariable",
            "id",
            "VercelProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_project_rels
    )

    # Assert Env Var referencing edge config is connected via REFERENCES
    # (EnvironmentVariable -REFERENCES-> EdgeConfig)
    expected_edgeconfig_rels = {
        ("env_123", "ecfg_123"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelEnvironmentVariable",
            "id",
            "VercelEdgeConfig",
            "id",
            "REFERENCES",
            rel_direction_right=True,
        )
        == expected_edgeconfig_rels
    )
