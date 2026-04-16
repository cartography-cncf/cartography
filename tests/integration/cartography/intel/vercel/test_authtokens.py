from unittest.mock import patch

import requests

import cartography.intel.vercel.authtokens
import tests.data.vercel.authtokens
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"


def _ensure_local_neo4j_has_test_auth_tokens(neo4j_session):
    cartography.intel.vercel.authtokens.load_auth_tokens(
        neo4j_session,
        tests.data.vercel.authtokens.VERCEL_AUTH_TOKENS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.authtokens,
    "get",
    return_value=tests.data.vercel.authtokens.VERCEL_AUTH_TOKENS,
)
def test_load_vercel_auth_tokens(mock_api, neo4j_session):
    """
    Ensure that auth tokens actually get loaded and connected
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
    cartography.intel.vercel.authtokens.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Auth Tokens exist
    expected_nodes = {
        ("tok_123",),
        ("tok_456",),
    }
    assert (
        check_nodes(neo4j_session, "VercelAuthToken", ["id"])
        == expected_nodes
    )

    # Assert Auth Tokens are connected to VercelTeam via RESOURCE
    expected_team_rels = {
        ("tok_123", TEST_TEAM_ID),
        ("tok_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelAuthToken",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_team_rels
    )
