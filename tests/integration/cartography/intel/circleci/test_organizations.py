from unittest.mock import patch

import requests

import cartography.intel.circleci.organizations
import tests.data.circleci.organizations
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"


def _ensure_local_neo4j_has_test_orgs(neo4j_session):
    orgs = cartography.intel.circleci.organizations.transform(
        tests.data.circleci.organizations.CIRCLECI_COLLABORATIONS,
    )
    cartography.intel.circleci.organizations.load_organizations(
        neo4j_session,
        orgs,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.circleci.organizations,
    "get",
    return_value=tests.data.circleci.organizations.CIRCLECI_COLLABORATIONS,
)
def test_load_circleci_organizations(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
    }

    # Act
    cartography.intel.circleci.organizations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert organizations exist with their slug
    assert check_nodes(neo4j_session, "CircleCIOrganization", ["id", "slug"]) == {
        ("org-1111-aaaa", "gh/acme"),
        ("org-2222-bbbb", "bb/beta"),
    }


@patch.object(
    cartography.intel.circleci.organizations,
    "get",
    return_value=tests.data.circleci.organizations.CIRCLECI_COLLABORATIONS,
)
def test_circleci_org_associated_with_github_org(mock_api, neo4j_session):
    """A GitHub-backed org links to its GitHubOrganization via ASSOCIATED_WITH."""
    # Arrange: the GitHub org login derived from slug "gh/acme" is "acme".
    neo4j_session.run("MERGE (o:GitHubOrganization {username: 'acme'})")
    api_session = requests.Session()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "BASE_URL": TEST_BASE_URL}

    # Act
    cartography.intel.circleci.organizations.sync(
        neo4j_session, api_session, common_job_parameters
    )

    # Assert (CircleCIOrganization)-[:ASSOCIATED_WITH]->(GitHubOrganization)
    assert check_rels(
        neo4j_session,
        "CircleCIOrganization",
        "id",
        "GitHubOrganization",
        "username",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        ("org-1111-aaaa", "acme"),
    }
