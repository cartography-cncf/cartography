from unittest.mock import patch

import requests

import cartography.intel.vercel.firewallconfigs
import tests.data.vercel.firewallconfigs
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
TEST_PROJECT_ID = "prj_abc"


def _ensure_local_neo4j_has_test_firewall_configs(neo4j_session):
    cartography.intel.vercel.firewallconfigs.load_firewall_configs(
        neo4j_session,
        tests.data.vercel.firewallconfigs.VERCEL_FIREWALL_CONFIGS,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.firewallconfigs,
    "get",
    return_value=tests.data.vercel.firewallconfigs.VERCEL_FIREWALL_CONFIGS,
)
def test_load_vercel_firewall_configs(mock_api, neo4j_session):
    """
    Ensure that firewall configs actually get loaded and linked to their project
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
        "project_id": TEST_PROJECT_ID,
    }
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.vercel.firewallconfigs.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        project_id=TEST_PROJECT_ID,
    )

    # Assert Firewall Configs exist
    expected_nodes = {
        ("prj_abc_firewall",),
    }
    assert check_nodes(neo4j_session, "VercelFirewallConfig", ["id"]) == expected_nodes

    # Assert Firewall Configs are connected to Project via RESOURCE
    # (Project -RESOURCE-> FirewallConfig)
    expected_rels = {
        ("prj_abc_firewall", TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelFirewallConfig",
            "id",
            "VercelProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
