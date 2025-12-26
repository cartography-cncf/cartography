"""Integration tests for GitLab groups module."""

from cartography.intel.gitlab.groups import load_groups
from tests.data.gitlab.groups import TEST_ORG_URL
from tests.data.gitlab.groups import TRANSFORMED_GROUPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _create_test_organization(neo4j_session):
    """Create test GitLabOrganization node."""
    neo4j_session.run(
        """
        MERGE (org:GitLabOrganization{id: $org_url})
        ON CREATE SET org.firstseen = timestamp()
        SET org.lastupdated = $update_tag,
            org.name = 'myorg'
        """,
        org_url=TEST_ORG_URL,
        update_tag=TEST_UPDATE_TAG,
    )


def test_load_gitlab_groups_nodes(neo4j_session):
    """Test that GitLab groups are loaded correctly into Neo4j."""
    # Arrange
    _create_test_organization(neo4j_session)

    # Act
    load_groups(
        neo4j_session,
        TRANSFORMED_GROUPS,
        TEST_ORG_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check that group nodes exist
    expected_nodes = {
        ("https://gitlab.example.com/myorg/platform", "Platform"),
        ("https://gitlab.example.com/myorg/apps", "Apps"),
        ("https://gitlab.example.com/myorg/platform/infrastructure", "Infrastructure"),
    }
    assert check_nodes(neo4j_session, "GitLabGroup", ["id", "name"]) == expected_nodes


def test_load_gitlab_groups_to_organization_relationships(neo4j_session):
    """Test that RESOURCE relationships to organization are created."""
    # Arrange
    _create_test_organization(neo4j_session)

    # Act
    load_groups(
        neo4j_session,
        TRANSFORMED_GROUPS,
        TEST_ORG_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check RESOURCE relationships from Organization to Group
    expected = {
        (TEST_ORG_URL, "https://gitlab.example.com/myorg/platform"),
        (TEST_ORG_URL, "https://gitlab.example.com/myorg/apps"),
        (TEST_ORG_URL, "https://gitlab.example.com/myorg/platform/infrastructure"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabOrganization",
            "id",
            "GitLabGroup",
            "id",
            "RESOURCE",
        )
        == expected
    )


def test_load_gitlab_groups_nested_relationships(neo4j_session):
    """Test that MEMBER_OF relationships for nested groups are created."""
    # Arrange
    _create_test_organization(neo4j_session)

    # Act
    load_groups(
        neo4j_session,
        TRANSFORMED_GROUPS,
        TEST_ORG_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check MEMBER_OF relationships for nested groups
    # Infrastructure is nested under Platform
    expected = {
        (
            "https://gitlab.example.com/myorg/platform/infrastructure",
            "https://gitlab.example.com/myorg/platform",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabGroup",
            "id",
            "GitLabGroup",
            "id",
            "MEMBER_OF",
        )
        == expected
    )


def test_load_gitlab_groups_properties(neo4j_session):
    """Test that group properties are loaded correctly."""
    # Arrange
    _create_test_organization(neo4j_session)

    # Act
    load_groups(
        neo4j_session,
        TRANSFORMED_GROUPS,
        TEST_ORG_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check all properties
    expected_nodes = {
        (
            "https://gitlab.example.com/myorg/platform",
            "Platform",
            "platform",
            "myorg/platform",
            "private",
        ),
        (
            "https://gitlab.example.com/myorg/apps",
            "Apps",
            "apps",
            "myorg/apps",
            "internal",
        ),
        (
            "https://gitlab.example.com/myorg/platform/infrastructure",
            "Infrastructure",
            "infrastructure",
            "myorg/platform/infrastructure",
            "private",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GitLabGroup",
            ["id", "name", "path", "full_path", "visibility"],
        )
        == expected_nodes
    )
