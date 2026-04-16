from unittest.mock import patch

import requests

import cartography.intel.vercel.securecomputenetworks
import tests.data.vercel.securecomputenetworks
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

# The sync function transforms raw API data by setting
# n["project_ids"] = [p["id"] for p in n.get("projects", [])].
# The stored data already has "project_ids" directly, so we construct a
# raw-shaped payload for the mocked `get` that the sync can transform.
_RAW_NETWORKS = [
    {
        **{k: v for k, v in n.items() if k != "project_ids"},
        "projects": [{"id": pid} for pid in n["project_ids"]],
    }
    for n in tests.data.vercel.securecomputenetworks.VERCEL_SECURE_COMPUTE_NETWORKS
]


def _ensure_local_neo4j_has_test_networks(neo4j_session):
    cartography.intel.vercel.securecomputenetworks.load_networks(
        neo4j_session,
        tests.data.vercel.securecomputenetworks.VERCEL_SECURE_COMPUTE_NETWORKS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.securecomputenetworks,
    "get",
    return_value=_RAW_NETWORKS,
)
def test_load_vercel_secure_compute_networks(mock_api, neo4j_session):
    """
    Ensure that secure compute networks actually get loaded and connected
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
    cartography.intel.vercel.securecomputenetworks.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Networks exist
    expected_nodes = {
        ("scn_123",),
        ("scn_456",),
    }
    assert (
        check_nodes(neo4j_session, "VercelSecureComputeNetwork", ["id"])
        == expected_nodes
    )

    # Assert Networks are connected to VercelTeam via RESOURCE
    expected_team_rels = {
        ("scn_123", TEST_TEAM_ID),
        ("scn_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelSecureComputeNetwork",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_team_rels
    )

    # Assert Networks are connected to VercelProject via CONNECTS
    expected_project_rels = {
        ("scn_123", "prj_abc"),
        ("scn_456", "prj_abc"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelSecureComputeNetwork",
            "id",
            "VercelProject",
            "id",
            "CONNECTS",
            rel_direction_right=True,
        )
        == expected_project_rels
    )
