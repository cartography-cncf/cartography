"""Integration tests for GitLab dependencies module."""

from cartography.intel.gitlab.dependencies import load_dependencies
from tests.data.gitlab.dependencies import TEST_PROJECT_URL
from tests.data.gitlab.dependencies import TRANSFORMED_DEPENDENCIES
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


def _create_test_dependency_file(neo4j_session, file_id: str, filename: str):
    """Create test GitLabDependencyFile node."""
    neo4j_session.run(
        """
        MERGE (df:GitLabDependencyFile{id: $file_id})
        ON CREATE SET df.firstseen = timestamp()
        SET df.lastupdated = $update_tag,
            df.filename = $filename,
            df.path = $filename
        """,
        file_id=file_id,
        filename=filename,
        update_tag=TEST_UPDATE_TAG,
    )


def test_load_gitlab_dependencies_nodes(neo4j_session):
    """Test that GitLab dependencies are loaded correctly into Neo4j."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_dependencies(
        neo4j_session,
        TRANSFORMED_DEPENDENCIES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check that dependency nodes exist
    expected_nodes = {
        (
            "https://gitlab.example.com/myorg/awesome-project:npm:express@4.18.2",
            "express",
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project:npm:lodash@4.17.21",
            "lodash",
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project:pypi:requests@2.31.0",
            "requests",
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project:golang:gin@1.9.1",
            "gin",
        ),
    }
    assert (
        check_nodes(neo4j_session, "GitLabDependency", ["id", "name"]) == expected_nodes
    )


def test_load_gitlab_dependencies_resource_relationships(neo4j_session):
    """Test that RESOURCE relationships to project are created."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_dependencies(
        neo4j_session,
        TRANSFORMED_DEPENDENCIES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check RESOURCE relationships from Project to Dependency
    expected = {
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project:npm:express@4.18.2",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project:npm:lodash@4.17.21",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project:pypi:requests@2.31.0",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project:golang:gin@1.9.1",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabProject",
            "id",
            "GitLabDependency",
            "id",
            "RESOURCE",
        )
        == expected
    )


def test_load_gitlab_dependencies_requires_relationships(neo4j_session):
    """Test that REQUIRES relationships from project to dependencies are created."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_dependencies(
        neo4j_session,
        TRANSFORMED_DEPENDENCIES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check REQUIRES relationships
    expected = {
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project:npm:express@4.18.2",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project:npm:lodash@4.17.21",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project:pypi:requests@2.31.0",
        ),
        (
            TEST_PROJECT_URL,
            "https://gitlab.example.com/myorg/awesome-project:golang:gin@1.9.1",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabProject",
            "id",
            "GitLabDependency",
            "id",
            "REQUIRES",
        )
        == expected
    )


def test_load_gitlab_dependencies_has_dep_relationships(neo4j_session):
    """Test that HAS_DEP relationships from dependency files are created."""
    # Arrange
    _create_test_project(neo4j_session)
    # Create dependency file that some dependencies reference
    manifest_id = "https://gitlab.example.com/myorg/awesome-project/blob/package.json"
    _create_test_dependency_file(neo4j_session, manifest_id, "package.json")

    # Act
    load_dependencies(
        neo4j_session,
        TRANSFORMED_DEPENDENCIES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check HAS_DEP relationships (only for deps with manifest_id)
    # Only express and lodash have manifest_id pointing to package.json
    expected = {
        (
            manifest_id,
            "https://gitlab.example.com/myorg/awesome-project:npm:express@4.18.2",
        ),
        (
            manifest_id,
            "https://gitlab.example.com/myorg/awesome-project:npm:lodash@4.17.21",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabDependencyFile",
            "id",
            "GitLabDependency",
            "id",
            "HAS_DEP",
        )
        == expected
    )


def test_load_gitlab_dependencies_properties(neo4j_session):
    """Test that dependency properties are loaded correctly."""
    # Arrange
    _create_test_project(neo4j_session)

    # Act
    load_dependencies(
        neo4j_session,
        TRANSFORMED_DEPENDENCIES,
        TEST_PROJECT_URL,
        TEST_UPDATE_TAG,
    )

    # Assert - Check all properties
    expected_nodes = {
        (
            "https://gitlab.example.com/myorg/awesome-project:npm:express@4.18.2",
            "express",
            "4.18.2",
            "npm",
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project:npm:lodash@4.17.21",
            "lodash",
            "4.17.21",
            "npm",
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project:pypi:requests@2.31.0",
            "requests",
            "2.31.0",
            "pypi",
        ),
        (
            "https://gitlab.example.com/myorg/awesome-project:golang:gin@1.9.1",
            "gin",
            "1.9.1",
            "golang",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GitLabDependency",
            ["id", "name", "version", "package_manager"],
        )
        == expected_nodes
    )
