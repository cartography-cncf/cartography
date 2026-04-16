from unittest.mock import patch

import requests

import cartography.intel.vercel.accessgroups
import tests.data.vercel.accessgroups
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


def _ensure_local_neo4j_has_test_access_groups(neo4j_session):
    cartography.intel.vercel.accessgroups.load_access_groups(
        neo4j_session,
        tests.data.vercel.accessgroups.VERCEL_ACCESS_GROUPS,
        TEST_TEAM_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.accessgroups,
    "get",
    return_value=tests.data.vercel.accessgroups.VERCEL_ACCESS_GROUPS,
)
def test_load_vercel_access_groups(mock_api, neo4j_session):
    """
    Ensure that access groups actually get loaded and connected
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
    }
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.vercel.accessgroups.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Access Groups exist
    expected_nodes = {
        ("ag_123",),
        ("ag_456",),
    }
    assert check_nodes(neo4j_session, "VercelAccessGroup", ["id"]) == expected_nodes

    # Assert Access Groups are connected to VercelTeam via RESOURCE
    expected_team_rels = {
        ("ag_123", TEST_TEAM_ID),
        ("ag_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelAccessGroup",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_team_rels
    )

    # Assert Access Groups are connected to VercelUser via HAS_MEMBER
    expected_user_rels = {
        ("ag_123", "user_homer"),
        ("ag_123", "user_marge"),
        ("ag_456", "user_homer"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelAccessGroup",
            "id",
            "VercelUser",
            "id",
            "HAS_MEMBER",
            rel_direction_right=True,
        )
        == expected_user_rels
    )

    # Assert Access Groups are connected to VercelProject via HAS_ACCESS_TO
    expected_project_rels = {
        ("ag_123", "prj_abc"),
        ("ag_456", "prj_abc"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelAccessGroup",
            "id",
            "VercelProject",
            "id",
            "HAS_ACCESS_TO",
            rel_direction_right=True,
        )
        == expected_project_rels
    )
