from unittest.mock import patch

import requests

import cartography.intel.vercel.users
import tests.data.vercel.users
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"


def _ensure_local_neo4j_has_test_users(neo4j_session):
    cartography.intel.vercel.users.load_users(
        neo4j_session,
        tests.data.vercel.users.VERCEL_USERS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.users,
    "get",
    return_value=tests.data.vercel.users.VERCEL_USERS,
)
def test_load_vercel_users(mock_api, neo4j_session):
    """
    Ensure that users actually get loaded and linked to their team
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
    cartography.intel.vercel.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Users exist
    expected_nodes = {
        ("user_homer", "homer@example.com"),
        ("user_marge", "marge@example.com"),
    }
    assert check_nodes(neo4j_session, "VercelUser", ["id", "email"]) == expected_nodes

    # Assert Users are connected with Team via RESOURCE (Team -RESOURCE-> User)
    expected_rels = {
        ("user_homer", TEST_TEAM_ID),
        ("user_marge", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelUser",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Users are also connected with Team via MEMBER_OF
    # (User -MEMBER_OF-> Team) carrying membership properties
    assert (
        check_rels(
            neo4j_session,
            "VercelUser",
            "id",
            "VercelTeam",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
