"""Integration tests for GitLab groups module."""

from cartography.intel.gitlab.groups import load_groups
from tests.data.gitlab.groups import TEST_GITLAB_URL
from tests.data.gitlab.groups import TEST_ORG_ID
from tests.data.gitlab.groups import TEST_ORG_URL
from tests.data.gitlab.groups import TRANSFORMED_GROUPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _create_test_organization(neo4j_session):
    """Create test GitLabOrganization node."""
    neo4j_session.run(
        """
        MERGE (org:GitLabOrganization{id: $org_id})
        ON CREATE SET org.firstseen = timestamp()
        SET org.lastupdated = $update_tag,
            org.name = 'myorg',
            org.web_url = $org_url,
            org.gitlab_url = $gitlab_url
        """,
        org_id=TEST_ORG_ID,
        org_url=TEST_ORG_URL,
        gitlab_url=TEST_GITLAB_URL,
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
        TEST_ORG_ID,
        TEST_GITLAB_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check that group nodes exist
    expected_nodes = {
        (20, "Platform"),
        (30, "Apps"),
        (40, "Infrastructure"),
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
        TEST_ORG_ID,
        TEST_GITLAB_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check RESOURCE relationships from Organization to Group
    expected = {
        (TEST_ORG_ID, 20),
        (TEST_ORG_ID, 30),
        (TEST_ORG_ID, 40),
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
        TEST_ORG_ID,
        TEST_GITLAB_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check MEMBER_OF relationships for nested groups
    # Infrastructure is nested under Platform
    expected = {
        (40, 20),
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
        TEST_ORG_ID,
        TEST_GITLAB_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check all properties
    expected_nodes = {
        (
            20,
            "Platform",
            "platform",
            "myorg/platform",
            "private",
        ),
        (
            30,
            "Apps",
            "apps",
            "myorg/apps",
            "internal",
        ),
        (
            40,
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
