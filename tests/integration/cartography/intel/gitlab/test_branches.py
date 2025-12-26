"""Integration tests for GitLab branches module."""

from cartography.intel.gitlab.branches import load_branches
from tests.data.gitlab.branches import TEST_PROJECT_URL
from tests.data.gitlab.branches import TRANSFORMED_BRANCHES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _create_test_project(neo4j_session):
    """Create test GitLabProject node."""
    neo4j_session.run(
        """
        MERGE (p:GitLabProject{id: $project_url})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $update_tag,
            p.name = 'awesome-project'
        """,
        project_url=TEST_PROJECT_URL,
        update_tag=TEST_UPDATE_TAG,
    )


def test_load_gitlab_branches_nodes(neo4j_session):
    """Test that GitLab branches are loaded correctly into Neo4j."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_branches(
        neo4j_session,
        TRANSFORMED_BRANCHES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check that branch nodes exist
    expected_nodes = {
        ("https://gitlab.example.com/myorg/awesome-project/tree/main", "main"),
        ("https://gitlab.example.com/myorg/awesome-project/tree/develop", "develop"),
        (
            "https://gitlab.example.com/myorg/awesome-project/tree/feature/new-api",
            "feature/new-api",
        ),
    }
    assert check_nodes(neo4j_session, "GitLabBranch", ["id", "name"]) == expected_nodes


def test_load_gitlab_branches_resource_relationships(neo4j_session):
    """Test that RESOURCE relationships to project are created."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_branches(
        neo4j_session,
        TRANSFORMED_BRANCHES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check RESOURCE relationships from Project to Branch
    expected = {
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/tree/main",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/tree/develop",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/tree/feature/new-api",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabProject",
            "id",
            "GitLabBranch",
            "id",
            "RESOURCE",
        )
        == expected
    )


def test_load_gitlab_branches_has_branch_relationships(neo4j_session):
    """Test that HAS_BRANCH relationships from project to branches are created."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_branches(
        neo4j_session,
        TRANSFORMED_BRANCHES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check HAS_BRANCH relationships
    expected = {
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/tree/main",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/tree/develop",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/tree/feature/new-api",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabProject",
            "id",
            "GitLabBranch",
            "id",
            "HAS_BRANCH",
        )
        == expected
    )


def test_load_gitlab_branches_properties(neo4j_session):
    """Test that branch properties are loaded correctly."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_branches(
        neo4j_session,
        TRANSFORMED_BRANCHES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check all properties
    expected_nodes = {
        (
            "https://gitlab.example.com/myorg/awesome-project/tree/main",
            "main",
            True,
            True,
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project/tree/develop",
            "develop",
            True,
            False,
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project/tree/feature/new-api",
            "feature/new-api",
            False,
            False,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GitLabBranch",
            ["id", "name", "protected", "default"],
        )
        == expected_nodes
    )
