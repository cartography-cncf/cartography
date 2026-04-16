from unittest.mock import patch

import requests

import cartography.intel.vercel.domains
import tests.data.vercel.domains
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"


def _ensure_local_neo4j_has_test_domains(neo4j_session):
    cartography.intel.vercel.domains.load_domains(
        neo4j_session,
        tests.data.vercel.domains.VERCEL_DOMAINS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.domains,
    "get",
    return_value=tests.data.vercel.domains.VERCEL_DOMAINS,
)
def test_load_vercel_domains(mock_api, neo4j_session):
    """
    Ensure that domains actually get loaded and linked to their team
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
    cartography.intel.vercel.domains.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Domains exist
    expected_nodes = {
        ("example.com",),
        ("example.org",),
    }
    assert check_nodes(neo4j_session, "VercelDomain", ["id"]) == expected_nodes

    # Assert Domains are connected to Team via RESOURCE (Team -RESOURCE-> Domain)
    expected_rels = {
        ("example.com", TEST_TEAM_ID),
        ("example.org", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelDomain",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
