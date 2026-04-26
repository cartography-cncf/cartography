from unittest.mock import patch

import requests

import cartography.intel.vercel.firewallbypassrules
import tests.data.vercel.firewallbypassrules
from tests.integration.cartography.intel.vercel.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
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
TEST_PROJECT_ID = "prj_abc"


def _ensure_local_neo4j_has_test_firewall_bypass_rules(neo4j_session):
    cartography.intel.vercel.firewallbypassrules.load_firewall_bypass_rules(
        neo4j_session,
        tests.data.vercel.firewallbypassrules.VERCEL_FIREWALL_BYPASS_RULES,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.firewallbypassrules,
    "get",
    return_value=tests.data.vercel.firewallbypassrules.VERCEL_FIREWALL_BYPASS_RULES,
)
def test_load_vercel_firewall_bypass_rules(mock_api, neo4j_session):
    """
    Ensure that firewall bypass rules actually get loaded and connected
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
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.vercel.firewallbypassrules.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        project_id=TEST_PROJECT_ID,
    )

    # Assert Firewall Bypass Rules exist
    expected_nodes = {
        ("fbr_123",),
        ("fbr_456",),
    }
    assert (
        check_nodes(neo4j_session, "VercelFirewallBypassRule", ["id"]) == expected_nodes
    )

    # Assert Firewall Bypass Rules are connected to VercelProject via RESOURCE
    expected_project_rels = {
        ("fbr_123", TEST_PROJECT_ID),
        ("fbr_456", TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelFirewallBypassRule",
            "id",
            "VercelProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_project_rels
    )

    # Assert Firewall Bypass Rules are connected to VercelUser via CREATED_BY
    expected_user_rels = {
        ("fbr_123", "user_homer"),
        ("fbr_456", "user_homer"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelFirewallBypassRule",
            "id",
            "VercelUser",
            "id",
            "CREATED_BY",
            rel_direction_right=True,
        )
        == expected_user_rels
    )
