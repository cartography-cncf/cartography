from unittest.mock import patch

import cartography.intel.socketdev.dependencies
import tests.data.socketdev.dependencies
from cartography.intel.socketdev.organizations import load_organizations
from cartography.intel.socketdev.organizations import transform as transform_orgs
from cartography.intel.socketdev.repositories import load_repositories
from cartography.intel.socketdev.repositories import transform as transform_repos
from tests.data.socketdev.organizations import ORGANIZATIONS_RESPONSE
from tests.data.socketdev.repositories import REPOSITORIES_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org-001"
TEST_ORG_SLUG = "acme-corp"


@patch.object(
    cartography.intel.socketdev.dependencies,
    "get",
    return_value=tests.data.socketdev.dependencies.DEPENDENCIES_RESPONSE["rows"],
)
def test_sync_dependencies(mock_api, neo4j_session):
    """
    Test that Socket.dev dependencies sync correctly and create proper nodes and relationships.
    """
    # Arrange: Load org and repos first
    orgs = transform_orgs(ORGANIZATIONS_RESPONSE)
    load_organizations(neo4j_session, orgs, TEST_UPDATE_TAG)

    repos = transform_repos(REPOSITORIES_RESPONSE["results"])
    load_repositories(neo4j_session, repos, TEST_ORG_ID, TEST_UPDATE_TAG)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
        "ORG_SLUG": TEST_ORG_SLUG,
    }

    # Act
    cartography.intel.socketdev.dependencies.sync_dependencies(
        neo4j_session,
        "fake-token",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Dependencies exist
    expected_dep_nodes = {
        ("dep-001", "lodash", "npm"),
        ("dep-002", "express", "npm"),
        ("dep-003", "requests", "pypi"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "SocketDevDependency",
            ["id", "name", "ecosystem"],
        )
        == expected_dep_nodes
    )

    # Assert: Dependencies are connected to Organization
    expected_org_rels = {
        ("dep-001", TEST_ORG_ID),
        ("dep-002", TEST_ORG_ID),
        ("dep-003", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SocketDevDependency",
            "id",
            "SocketDevOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_org_rels
    )

    # Assert: Dependencies are connected to Repositories
    expected_repo_rels = {
        ("dep-001", "acme-corp/frontend-app"),
        ("dep-002", "acme-corp/backend-api"),
        ("dep-003", "acme-corp/backend-api"),
    }
    assert (
        check_rels(
            neo4j_session,
            "SocketDevDependency",
            "id",
            "SocketDevRepository",
            "fullname",
            "FOUND_IN",
            rel_direction_right=True,
        )
        == expected_repo_rels
    )
