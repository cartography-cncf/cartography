"""Integration tests for GitLab dependency files module."""

from cartography.intel.gitlab.dependency_files import load_dependency_files
from tests.data.gitlab.dependency_files import TEST_PROJECT_URL
from tests.data.gitlab.dependency_files import TRANSFORMED_DEPENDENCY_FILES
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


def test_load_gitlab_dependency_files_nodes(neo4j_session):
    """Test that GitLab dependency files are loaded correctly into Neo4j."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_dependency_files(
        neo4j_session,
        TRANSFORMED_DEPENDENCY_FILES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check that dependency file nodes exist
    expected_nodes = {
        (
            "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
            "package.json",
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project/blob/backend/requirements.txt",
            "requirements.txt",
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project/blob/services/api/go.mod",
            "go.mod",
        ),
    }
    assert (
        check_nodes(neo4j_session, "GitLabDependencyFile", ["id", "filename"])
        == expected_nodes
    )


def test_load_gitlab_dependency_files_resource_relationships(neo4j_session):
    """Test that RESOURCE relationships to project are created."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_dependency_files(
        neo4j_session,
        TRANSFORMED_DEPENDENCY_FILES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check RESOURCE relationships from Project to DependencyFile
    expected = {
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/blob/backend/requirements.txt",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/blob/services/api/go.mod",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabProject",
            "id",
            "GitLabDependencyFile",
            "id",
            "RESOURCE",
        )
        == expected
    )


def test_load_gitlab_dependency_files_has_dependency_file_relationships(neo4j_session):
    """Test that HAS_DEPENDENCY_FILE relationships from project are created."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_dependency_files(
        neo4j_session,
        TRANSFORMED_DEPENDENCY_FILES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check HAS_DEPENDENCY_FILE relationships
    expected = {
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/blob/backend/requirements.txt",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project/blob/services/api/go.mod",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabProject",
            "id",
            "GitLabDependencyFile",
            "id",
            "HAS_DEPENDENCY_FILE",
        )
        == expected
    )


def test_load_gitlab_dependency_files_properties(neo4j_session):
    """Test that dependency file properties are loaded correctly."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_dependency_files(
        neo4j_session,
        TRANSFORMED_DEPENDENCY_FILES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check all properties
    expected_nodes = {
        (
            "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
            "package.json",
            "package.json",
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project/blob/backend/requirements.txt",
            "backend/requirements.txt",
            "requirements.txt",
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project/blob/services/api/go.mod",
            "services/api/go.mod",
            "go.mod",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GitLabDependencyFile",
            ["id", "path", "filename"],
        )
        == expected_nodes
    )
