from unittest.mock import patch

import requests

import cartography.intel.vercel.sharedenvironmentvariables
import tests.data.vercel.sharedenvironmentvariables
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"


def _ensure_local_neo4j_has_test_shared_env_vars(neo4j_session):
    cartography.intel.vercel.sharedenvironmentvariables.load_shared_env_vars(
        neo4j_session,
        tests.data.vercel.sharedenvironmentvariables.VERCEL_SHARED_ENVIRONMENT_VARIABLES,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.sharedenvironmentvariables,
    "get",
    return_value=tests.data.vercel.sharedenvironmentvariables.VERCEL_SHARED_ENVIRONMENT_VARIABLES,
)
def test_load_vercel_shared_environment_variables(mock_api, neo4j_session):
    """
    Ensure that shared environment variables actually get loaded and linked to their team
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
    cartography.intel.vercel.sharedenvironmentvariables.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Shared Env Vars exist
    expected_nodes = {
        ("senv_123",),
        ("senv_456",),
    }
    assert (
        check_nodes(neo4j_session, "VercelSharedEnvironmentVariable", ["id"])
        == expected_nodes
    )

    # Assert Shared Env Vars are connected to Team via RESOURCE
    # (Team -RESOURCE-> SharedEnvironmentVariable)
    expected_rels = {
        ("senv_123", TEST_TEAM_ID),
        ("senv_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelSharedEnvironmentVariable",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
