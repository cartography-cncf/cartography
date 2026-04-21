from unittest.mock import patch

import cartography.intel.socketdev.repositories
import tests.data.socketdev.repositories
from cartography.intel.socketdev.organizations import load_organizations
from cartography.intel.socketdev.organizations import transform as transform_orgs
from tests.data.socketdev.organizations import ORGANIZATIONS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org-001"
TEST_ORG_SLUG = "acme-corp"


@patch.object(
    cartography.intel.socketdev.repositories,
    "get",
    return_value=tests.data.socketdev.repositories.REPOSITORIES_RESPONSE["results"],
)
def test_sync_repositories(mock_api, neo4j_session):
    """
    Test that Socket.dev repositories sync correctly and create proper nodes and relationships.
    """
    # Arrange: Load the organization first (repos need it for the sub_resource_relationship)
    orgs = transform_orgs(ORGANIZATIONS_RESPONSE)
    load_organizations(neo4j_session, orgs, TEST_UPDATE_TAG)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
        "ORG_SLUG": TEST_ORG_SLUG,
    }

    # Act
    cartography.intel.socketdev.repositories.sync_repositories(
        neo4j_session,
        "fake-token",
        TEST_ORG_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: Organization exists
    expected_org_nodes = {
        (TEST_ORG_ID, TEST_ORG_SLUG),
    }
    assert (
        check_nodes(neo4j_session, "SocketDevOrganization", ["id", "slug"])
        == expected_org_nodes
    )

    # Assert: Repositories exist with fullname
    expected_repo_nodes = {
        ("repo-001", "frontend-app", "acme-corp/frontend-app"),
        ("repo-002", "backend-api", "acme-corp/backend-api"),
    }
    assert (
        check_nodes(neo4j_session, "SocketDevRepository", ["id", "slug", "fullname"])
        == expected_repo_nodes
    )

    # Assert: Repositories are connected to Organization
    expected_rels = {
        ("repo-001", TEST_ORG_ID),
        ("repo-002", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SocketDevRepository",
            "id",
            "SocketDevOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
