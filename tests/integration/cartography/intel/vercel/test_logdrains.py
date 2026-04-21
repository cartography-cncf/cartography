from unittest.mock import patch

import requests

import cartography.intel.vercel.logdrains
import tests.data.vercel.logdrains
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


def _ensure_local_neo4j_has_test_log_drains(neo4j_session):
    cartography.intel.vercel.logdrains.load_log_drains(
        neo4j_session,
        tests.data.vercel.logdrains.VERCEL_LOG_DRAINS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.logdrains,
    "get",
    return_value=tests.data.vercel.logdrains.VERCEL_LOG_DRAINS,
)
def test_load_vercel_log_drains(mock_api, neo4j_session):
    """
    Ensure that log drains actually get loaded and connected
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
    cartography.intel.vercel.logdrains.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Log Drains exist
    expected_nodes = {
        ("ld_123",),
        ("ld_456",),
    }
    assert check_nodes(neo4j_session, "VercelLogDrain", ["id"]) == expected_nodes

    # Assert Log Drains are connected to VercelTeam via RESOURCE
    expected_team_rels = {
        ("ld_123", TEST_TEAM_ID),
        ("ld_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelLogDrain",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_team_rels
    )

    # Assert Log Drains are connected to VercelProject via MONITORS
    expected_project_rels = {
        ("ld_123", "prj_def"),
        ("ld_456", "prj_def"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelLogDrain",
            "id",
            "VercelProject",
            "id",
            "MONITORS",
            rel_direction_right=True,
        )
        == expected_project_rels
    )
