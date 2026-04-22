from unittest.mock import patch

import requests

import cartography.intel.vercel.teams
import tests.data.vercel.teams
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"


def _ensure_local_neo4j_has_test_teams(neo4j_session):
    cartography.intel.vercel.teams.load_teams(
        neo4j_session,
        [tests.data.vercel.teams.VERCEL_TEAM],
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.teams,
    "get",
    return_value=tests.data.vercel.teams.VERCEL_TEAM,
)
def test_load_vercel_teams(mock_api, neo4j_session):
    """
    Ensure that teams actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
    }

    # Act
    cartography.intel.vercel.teams.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Teams exist
    expected_nodes = {
        (TEST_TEAM_ID,),
    }
    assert check_nodes(neo4j_session, "VercelTeam", ["id"]) == expected_nodes
