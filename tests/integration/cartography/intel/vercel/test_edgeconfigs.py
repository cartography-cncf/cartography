from unittest.mock import patch

import requests

import cartography.intel.vercel.edgeconfigs
import tests.data.vercel.edgeconfigs
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"


def _ensure_local_neo4j_has_test_edge_configs(neo4j_session):
    cartography.intel.vercel.edgeconfigs.load_edge_configs(
        neo4j_session,
        tests.data.vercel.edgeconfigs.VERCEL_EDGE_CONFIGS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.edgeconfigs,
    "get",
    return_value=tests.data.vercel.edgeconfigs.VERCEL_EDGE_CONFIGS,
)
def test_load_vercel_edge_configs(mock_api, neo4j_session):
    """
    Ensure that edge configs actually get loaded and connected
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
    cartography.intel.vercel.edgeconfigs.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Edge Configs exist
    expected_nodes = {
        ("ecfg_123",),
        ("ecfg_456",),
    }
    assert check_nodes(neo4j_session, "VercelEdgeConfig", ["id"]) == expected_nodes

    # Assert Edge Configs are connected to VercelTeam via RESOURCE
    expected_team_rels = {
        ("ecfg_123", TEST_TEAM_ID),
        ("ecfg_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelEdgeConfig",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_team_rels
    )
