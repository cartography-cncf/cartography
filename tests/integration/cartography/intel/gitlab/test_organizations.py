"""Integration tests for GitLab organizations module."""

from cartography.intel.gitlab.organizations import cleanup_organizations
from cartography.intel.gitlab.organizations import load_organizations
from tests.data.gitlab.organizations import TRANSFORMED_ORGANIZATION
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_GITLAB_URL = "https://gitlab.example.com"


def test_load_gitlab_organization_nodes(neo4j_session):
    """Test that GitLab organization is loaded correctly into Neo4j."""
    # Act
    load_organizations(
        neo4j_session,
        [TRANSFORMED_ORGANIZATION],
        TEST_UPDATE_TAG,
    )

    # Assert - Check that organization node exists
    expected_nodes = {
        ("https://gitlab.example.com/myorg", "MyOrg"),
    }
    assert (
        check_nodes(neo4j_session, "GitLabOrganization", ["id", "name"])
        == expected_nodes
    )


def test_load_gitlab_organization_properties(neo4j_session):
    """Test that organization properties are loaded correctly."""
    # Act
    load_organizations(
        neo4j_session,
        [TRANSFORMED_ORGANIZATION],
        TEST_UPDATE_TAG,
    )

    # Assert - Check all properties
    expected_nodes = {
        (
            "https://gitlab.example.com/myorg",
            "MyOrg",
            "myorg",
            "myorg",
            "private",
            "https://gitlab.example.com",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GitLabOrganization",
            ["id", "name", "path", "full_path", "visibility", "gitlab_url"],
        )
        == expected_nodes
    )


def test_cleanup_gitlab_organizations(neo4j_session):
    """
    Test that cleanup_organizations runs without error.

    Note: GitLabOrganization is not a sub resource, so cleanup
    currently doesn't delete stale nodes. This test verifies the function
    executes cleanly without errors.
    """
    # Arrange - Load an organization
    load_organizations(
        neo4j_session,
        [TRANSFORMED_ORGANIZATION],
        TEST_UPDATE_TAG,
    )

    # Verify organization exists
    assert check_nodes(neo4j_session, "GitLabOrganization", ["id"]) == {
        ("https://gitlab.example.com/myorg",),
    }

    # Act - Run cleanup with a different UPDATE_TAG (simulating stale data)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG + 1}
    cleanup_organizations(neo4j_session, common_job_parameters, TEST_GITLAB_URL)

    # Assert - Organization still exists (no cleanup logic for top-level orgs)
    # This documents current behavior: orgs are not auto-cleaned as they have
    # no sub_resource_relationship to scope cleanup
    assert check_nodes(neo4j_session, "GitLabOrganization", ["id"]) == {
        ("https://gitlab.example.com/myorg",),
    }
