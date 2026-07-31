from unittest.mock import patch

import requests

import cartography.intel.nullify.teams
import tests.data.nullify.teams
from tests.integration.cartography.intel.nullify.test_repositories import (
    _ensure_local_neo4j_has_test_repositories,
)
from tests.integration.cartography.intel.nullify.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT = "acme"


@patch.object(
    cartography.intel.nullify.teams,
    "get",
    return_value=tests.data.nullify.teams.NULLIFY_TEAMS,
)
def test_load_nullify_teams(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT,
        "BASE_URL": "https://api.acme.nullify.ai",
    }
    _ensure_local_neo4j_has_test_repositories(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.nullify.teams.sync(
        neo4j_session,
        api_session,
        "https://api.acme.nullify.ai",
        TEST_TENANT,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert teams exist
    assert check_nodes(neo4j_session, "NullifyTeam", ["id", "name"]) == {
        ("T1", "Platform"),
        ("T2", "Security"),
    }

    # Assert teams are scoped to the tenant
    assert check_rels(
        neo4j_session,
        "NullifyTeam",
        "id",
        "NullifyTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("T1", TEST_TENANT),
        ("T2", TEST_TENANT),
    }

    # Assert teams own their repositories (repositoryIds one-to-many)
    assert check_rels(
        neo4j_session,
        "NullifyTeam",
        "id",
        "NullifyRepository",
        "repository_id",
        "OWNS",
        rel_direction_right=True,
    ) == {
        ("T1", "R1"),
        ("T1", "R2"),
        ("T2", "R1"),
    }

    # Assert team membership (memberIds one-to-many, user -> team)
    assert check_rels(
        neo4j_session,
        "NullifyUser",
        "id",
        "NullifyTeam",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("U1", "T1"),
        ("U2", "T1"),
        ("U2", "T2"),
    }

    # Assert team leads (leadId, user -> team)
    assert check_rels(
        neo4j_session,
        "NullifyUser",
        "id",
        "NullifyTeam",
        "id",
        "LEADS",
        rel_direction_right=True,
    ) == {
        ("U1", "T1"),
        ("U2", "T2"),
    }
