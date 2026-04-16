from unittest.mock import patch

import requests

import cartography.intel.vercel.aliases
import tests.data.vercel.aliases
from tests.integration.cartography.intel.vercel.test_deployments import (
    _ensure_local_neo4j_has_test_deployments,
)
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


def _ensure_local_neo4j_has_test_aliases(neo4j_session):
    cartography.intel.vercel.aliases.load_aliases(
        neo4j_session,
        tests.data.vercel.aliases.VERCEL_ALIASES,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.aliases,
    "get",
    return_value=tests.data.vercel.aliases.VERCEL_ALIASES,
)
def test_load_vercel_aliases(mock_api, neo4j_session):
    """
    Ensure that aliases actually get loaded and connected
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
    _ensure_local_neo4j_has_test_deployments(neo4j_session)

    # Act
    cartography.intel.vercel.aliases.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Aliases exist
    expected_nodes = {
        ("als_123",),
        ("als_456",),
    }
    assert check_nodes(neo4j_session, "VercelAlias", ["id"]) == expected_nodes

    # Assert Aliases are connected to VercelTeam via RESOURCE
    expected_team_rels = {
        ("als_123", TEST_TEAM_ID),
        ("als_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelAlias",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_team_rels
    )

    # Assert Aliases are connected to VercelDeployment via DEPLOYED_TO
    expected_deployment_rels = {
        ("als_123", "dpl_123"),
        ("als_456", "dpl_123"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelAlias",
            "id",
            "VercelDeployment",
            "id",
            "DEPLOYED_TO",
            rel_direction_right=True,
        )
        == expected_deployment_rels
    )

    # Assert Aliases are connected to VercelProject via BELONGS_TO_PROJECT
    expected_project_rels = {
        ("als_123", "prj_abc"),
        ("als_456", "prj_abc"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelAlias",
            "id",
            "VercelProject",
            "id",
            "BELONGS_TO_PROJECT",
            rel_direction_right=True,
        )
        == expected_project_rels
    )
