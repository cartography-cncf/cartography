from unittest.mock import patch

import requests

import cartography.intel.vercel.integrations
import tests.data.vercel.integrations
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


def _ensure_local_neo4j_has_test_integrations(neo4j_session):
    cartography.intel.vercel.integrations.load_integrations(
        neo4j_session,
        tests.data.vercel.integrations.VERCEL_INTEGRATIONS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.integrations,
    "get",
    return_value=tests.data.vercel.integrations.VERCEL_INTEGRATIONS,
)
def test_load_vercel_integrations(mock_api, neo4j_session):
    """
    Ensure that integrations actually get loaded and connected
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
    }
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.vercel.integrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Integrations exist
    expected_nodes = {
        ("icfg_123",),
        ("icfg_456",),
    }
    assert check_nodes(neo4j_session, "VercelIntegration", ["id"]) == expected_nodes

    # Assert Integrations are connected to VercelTeam via RESOURCE
    expected_team_rels = {
        ("icfg_123", TEST_TEAM_ID),
        ("icfg_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelIntegration",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_team_rels
    )

    # Assert Integrations are connected to VercelProject via CONFIGURED_FOR
    expected_project_rels = {
        ("icfg_123", "prj_abc"),
        ("icfg_123", "prj_def"),
        ("icfg_456", "prj_abc"),
        ("icfg_456", "prj_def"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelIntegration",
            "id",
            "VercelProject",
            "id",
            "CONFIGURED_FOR",
            rel_direction_right=True,
        )
        == expected_project_rels
    )
