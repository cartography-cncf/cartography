from unittest.mock import patch

import requests

import cartography.intel.vercel.projectdomains
import tests.data.vercel.projectdomains
from tests.integration.cartography.intel.vercel.test_domains import (
    _ensure_local_neo4j_has_test_domains,
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
TEST_PROJECT_ID = "prj_abc"


def _ensure_local_neo4j_has_test_project_domains(neo4j_session):
    cartography.intel.vercel.projectdomains.load_project_domains(
        neo4j_session,
        tests.data.vercel.projectdomains.VERCEL_PROJECT_DOMAINS,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.projectdomains,
    "get",
    return_value=tests.data.vercel.projectdomains.VERCEL_PROJECT_DOMAINS,
)
def test_load_vercel_project_domains(mock_api, neo4j_session):
    """
    Ensure that project domains actually get loaded and linked to their
    project and backing Vercel domain
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
    _ensure_local_neo4j_has_test_domains(neo4j_session)

    # Act
    cartography.intel.vercel.projectdomains.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        project_id=TEST_PROJECT_ID,
    )

    # Assert Project Domains exist
    expected_nodes = {
        ("pdom_123",),
        ("pdom_456",),
    }
    assert (
        check_nodes(neo4j_session, "VercelProjectDomain", ["id"])
        == expected_nodes
    )

    # Assert Project Domains are connected to Project via RESOURCE
    # (Project -RESOURCE-> ProjectDomain)
    expected_project_rels = {
        ("pdom_123", TEST_PROJECT_ID),
        ("pdom_456", TEST_PROJECT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelProjectDomain",
            "id",
            "VercelProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_project_rels
    )

    # Assert Project Domains are connected to Domain via USES_DOMAIN
    # (ProjectDomain -USES_DOMAIN-> Domain)
    expected_domain_rels = {
        ("pdom_123", "example.com"),
        ("pdom_456", "example.org"),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelProjectDomain",
            "id",
            "VercelDomain",
            "id",
            "USES_DOMAIN",
            rel_direction_right=True,
        )
        == expected_domain_rels
    )
