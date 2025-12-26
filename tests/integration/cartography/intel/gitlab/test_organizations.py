"""Integration tests for GitLab organizations module."""

from cartography.intel.gitlab.organizations import load_organizations
from tests.data.gitlab.organizations import TRANSFORMED_ORGANIZATION
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


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
