from unittest.mock import patch

import requests

import cartography.intel.vercel.webhooks
import tests.data.vercel.webhooks
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


def _ensure_local_neo4j_has_test_webhooks(neo4j_session):
    cartography.intel.vercel.webhooks.load_webhooks(
        neo4j_session,
        tests.data.vercel.webhooks.VERCEL_WEBHOOKS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.webhooks,
    "get",
    return_value=tests.data.vercel.webhooks.VERCEL_WEBHOOKS,
)
def test_load_vercel_webhooks(mock_api, neo4j_session):
    """
    Ensure that webhooks actually get loaded and connected
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
    }
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.vercel.webhooks.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Webhooks exist
    expected_nodes = {
        ("whk_123",),
        ("whk_456",),
    }
    assert check_nodes(neo4j_session, "VercelWebhook", ["id"]) == expected_nodes

    # Assert Webhooks are connected to VercelTeam via RESOURCE
    expected_team_rels = {
        ("whk_123", TEST_TEAM_ID),
        ("whk_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelWebhook",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_team_rels
    )

    # Assert Webhooks are connected to VercelProject via WATCHES
    expected_project_rels = {
        ("whk_123", "prj_abc"),
        ("whk_456", "prj_abc"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelWebhook",
            "id",
            "VercelProject",
            "id",
            "WATCHES",
            rel_direction_right=True,
        )
        == expected_project_rels
    )
