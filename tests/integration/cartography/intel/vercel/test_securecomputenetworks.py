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
    return_value=tests.data.vercel.securecomputenetworks.VERCEL_RAW_NETWORKS,
)
def test_load_vercel_secure_compute_networks(mock_api, neo4j_session):
    """
    Ensure networks are loaded, and that per-project attachments carry the
    per-environment scope and passive mode derived from
    project.connectConfigurations.
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
        tests.data.vercel.securecomputenetworks.VERCEL_PROJECTS_WITH_CONNECT_CONFIG,
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

    # Assert CONNECTS rels carry environments + passive_environments
    result = neo4j_session.run(
        """
        MATCH (n:VercelSecureComputeNetwork)-[r:CONNECTS]->(p:VercelProject)
        RETURN n.id AS network_id,
               p.id AS project_id,
               r.environments AS environments,
               r.passive_environments AS passive_environments
        """
    )
    actual = {
        (
            record["network_id"],
            record["project_id"],
            tuple(sorted(record["environments"])),
            tuple(sorted(record["passive_environments"])),
        )
        for record in result
    }
    expected = {
        (
            "scn_123",
            "prj_abc",
            ("preview", "production"),
            ("preview",),
        ),
        (
            "scn_456",
            "prj_abc",
            ("development",),
            (),
        ),
    }
    assert actual == expected
