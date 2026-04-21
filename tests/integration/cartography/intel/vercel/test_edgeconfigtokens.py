from unittest.mock import patch

import requests

import cartography.intel.vercel.edgeconfigtokens
import tests.data.vercel.edgeconfigtokens
from tests.integration.cartography.intel.vercel.test_edgeconfigs import (
    _ensure_local_neo4j_has_test_edge_configs,
)
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"
TEST_EDGE_CONFIG_ID = "ecfg_123"


def _ensure_local_neo4j_has_test_edge_config_tokens(neo4j_session):
    cartography.intel.vercel.edgeconfigtokens.load_edge_config_tokens(
        neo4j_session,
        tests.data.vercel.edgeconfigtokens.VERCEL_EDGE_CONFIG_TOKENS,
        TEST_TEAM_ID,
        TEST_EDGE_CONFIG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.edgeconfigtokens,
    "get",
    return_value=tests.data.vercel.edgeconfigtokens.VERCEL_EDGE_CONFIG_TOKENS,
)
def test_load_vercel_edge_config_tokens(mock_api, neo4j_session):
    """
    Ensure that edge config tokens actually get loaded and connected
    """

    # Arrange
    api_session = requests.Session()
    ec_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
        "edge_config_id": TEST_EDGE_CONFIG_ID,
    }
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_edge_configs(neo4j_session)

    # Act
    cartography.intel.vercel.edgeconfigtokens.sync(
        neo4j_session,
        api_session,
        ec_job_parameters,
        edge_config_id=TEST_EDGE_CONFIG_ID,
    )

    # Assert Edge Config Tokens exist
    expected_nodes = {
        ("ect_123",),
        ("ect_456",),
    }
    assert check_nodes(neo4j_session, "VercelEdgeConfigToken", ["id"]) == expected_nodes

    # Assert Edge Config Tokens are connected to Team via RESOURCE
    # (Team -RESOURCE-> Token)
    expected_team_rels = {
        ("ect_123", TEST_TEAM_ID),
        ("ect_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelEdgeConfigToken",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_team_rels
    )

    # Assert Edge Config Tokens are connected to VercelEdgeConfig via HAS_TOKEN
    # (EdgeConfig -HAS_TOKEN-> Token)
    expected_edge_config_rels = {
        ("ect_123", TEST_EDGE_CONFIG_ID),
        ("ect_456", TEST_EDGE_CONFIG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelEdgeConfigToken",
            "id",
            "VercelEdgeConfig",
            "id",
            "HAS_TOKEN",
            rel_direction_right=False,
        )
        == expected_edge_config_rels
    )
