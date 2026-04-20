from unittest.mock import patch

import requests

import cartography.intel.vercel.authtokens
import tests.data.vercel.authtokens
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


def _ensure_local_neo4j_has_test_auth_tokens(neo4j_session):
    cartography.intel.vercel.authtokens.load_auth_tokens(
        neo4j_session,
        tests.data.vercel.authtokens.VERCEL_AUTH_TOKENS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.authtokens,
    "get_caller_id",
    return_value=tests.data.vercel.authtokens.VERCEL_CALLER_USER_ID,
)
@patch.object(
    cartography.intel.vercel.authtokens,
    "get",
    return_value=tests.data.vercel.authtokens.VERCEL_RAW_AUTH_TOKENS,
)
def test_load_vercel_auth_tokens(mock_get, mock_caller, neo4j_session):
    """
    Ensure that auth tokens actually get loaded, filtered to the team's scope,
    and linked to both the team and the owning user.
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
    }
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.vercel.authtokens.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert only team-scoped tokens are kept (user-only and other-team dropped)
    expected_nodes = {
        ("tok_team",),
        ("tok_mixed",),
    }
    assert check_nodes(neo4j_session, "VercelAuthToken", ["id"]) == expected_nodes

    # Assert Auth Tokens are connected to VercelTeam via RESOURCE
    expected_team_rels = {
        ("tok_team", TEST_TEAM_ID),
        ("tok_mixed", TEST_TEAM_ID),
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

    # Assert Auth Tokens are connected to the owning VercelUser via OWNED_BY
    expected_user_rels = {
        ("tok_team", tests.data.vercel.authtokens.VERCEL_CALLER_USER_ID),
        ("tok_mixed", tests.data.vercel.authtokens.VERCEL_CALLER_USER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelAuthToken",
            "id",
            "VercelUser",
            "id",
            "OWNED_BY",
            rel_direction_right=True,
        )
        == expected_user_rels
    )
