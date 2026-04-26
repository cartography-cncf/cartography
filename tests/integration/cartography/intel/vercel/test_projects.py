from unittest.mock import patch

import requests

import cartography.intel.vercel.projects
import tests.data.vercel.projects
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"


def _ensure_local_neo4j_has_test_projects(neo4j_session):
    cartography.intel.vercel.projects.load_projects(
        neo4j_session,
        tests.data.vercel.projects.VERCEL_PROJECTS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.projects,
    "get",
    return_value=tests.data.vercel.projects.VERCEL_PROJECTS,
)
def test_load_vercel_projects(mock_api, neo4j_session):
    """
    Ensure that projects actually get loaded and linked to their team
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
    }
    _ensure_local_neo4j_has_test_teams(neo4j_session)

    # Act
    cartography.intel.vercel.projects.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Projects exist
    expected_nodes = {
        ("prj_abc",),
        ("prj_def",),
    }
    assert check_nodes(neo4j_session, "VercelProject", ["id"]) == expected_nodes

    # Assert Projects are connected with Team via RESOURCE (Team -RESOURCE-> Project)
    expected_rels = {
        ("prj_abc", TEST_TEAM_ID),
        ("prj_def", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelProject",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
