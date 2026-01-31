"""
Integration tests for GitHub Container Packages sync.
"""

import cartography.intel.github.container_packages
import tests.data.github.container_packages
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


TEST_UPDATE_TAG = 123456789
TEST_ORG_URL = "https://github.com/test-org"
TEST_API_URL = "https://api.github.com"
TEST_ORG = "test-org"


def test_sync_container_packages(neo4j_session):
    """
    Test that container packages are correctly synced to the graph.
    """
    # Arrange: Transform test data
    transformed_packages = (
        cartography.intel.github.container_packages.transform_container_packages(
            tests.data.github.container_packages.GET_CONTAINER_PACKAGES,
            TEST_ORG_URL,
        )
    )

    # Act: Load the data
    cartography.intel.github.container_packages.load_container_packages(
        neo4j_session,
        transformed_packages,
        TEST_ORG_URL,
        TEST_UPDATE_TAG,
    )

    # Assert: Verify nodes were created
    expected_nodes = {
        ("123456", "my-app", "container", "public"),
        ("123457", "backend-service", "container", "private"),
        ("123458", "frontend-app", "container", "public"),
    }

    nodes = neo4j_session.run(
        """
        MATCH (p:GitHubContainerPackage)
        RETURN p.id, p.name, p.package_type, p.visibility
        """
    )

    actual_nodes = {
        (
            str(node["p.id"]),
            node["p.name"],
            node["p.package_type"],
            node["p.visibility"],
        )
        for node in nodes
    }

    assert actual_nodes == expected_nodes


def test_container_packages_have_container_registry_label(neo4j_session):
    """
    Test that container packages have the ContainerRegistry label.
    """
    # Arrange & Act
    transformed_packages = (
        cartography.intel.github.container_packages.transform_container_packages(
            tests.data.github.container_packages.GET_CONTAINER_PACKAGES,
            TEST_ORG_URL,
        )
    )

    cartography.intel.github.container_packages.load_container_packages(
        neo4j_session,
        transformed_packages,
        TEST_ORG_URL,
        TEST_UPDATE_TAG,
    )

    # Assert: Verify ContainerRegistry label exists
    nodes = neo4j_session.run(
        """
        MATCH (p:GitHubContainerPackage:ContainerRegistry)
        RETURN count(p) as count
        """
    )

    result = nodes.single()
    assert result["count"] == 3


def test_container_packages_repository_relationship(neo4j_session):
    """
    Test that container packages have correct repository information.
    """
    # Arrange & Act
    transformed_packages = (
        cartography.intel.github.container_packages.transform_container_packages(
            tests.data.github.container_packages.GET_CONTAINER_PACKAGES,
            TEST_ORG_URL,
        )
    )

    cartography.intel.github.container_packages.load_container_packages(
        neo4j_session,
        transformed_packages,
        TEST_ORG_URL,
        TEST_UPDATE_TAG,
    )

    # Assert: Verify repository information
    nodes = neo4j_session.run(
        """
        MATCH (p:GitHubContainerPackage {name: 'my-app'})
        RETURN p.repository_id, p.repository_name
        """
    )

    result = nodes.single()
    assert result["p.repository_id"] == 456789
    assert result["p.repository_name"] == "test-org/my-app-repo"


def test_container_packages_without_repository(neo4j_session):
    """
    Test that container packages without linked repositories are handled correctly.
    """
    # Arrange & Act
    transformed_packages = (
        cartography.intel.github.container_packages.transform_container_packages(
            tests.data.github.container_packages.GET_CONTAINER_PACKAGES,
            TEST_ORG_URL,
        )
    )

    cartography.intel.github.container_packages.load_container_packages(
        neo4j_session,
        transformed_packages,
        TEST_ORG_URL,
        TEST_UPDATE_TAG,
    )

    # Assert: Verify package without repository has null repository fields
    nodes = neo4j_session.run(
        """
        MATCH (p:GitHubContainerPackage {name: 'frontend-app'})
        RETURN p.repository_id, p.repository_name
        """
    )

    result = nodes.single()
    assert result["p.repository_id"] is None
    assert result["p.repository_name"] is None


def test_container_packages_cleanup(neo4j_session):
    """
    Test that cleanup removes stale container packages.
    """
    # Arrange: Load initial data
    transformed_packages = (
        cartography.intel.github.container_packages.transform_container_packages(
            tests.data.github.container_packages.GET_CONTAINER_PACKAGES,
            TEST_ORG_URL,
        )
    )

    cartography.intel.github.container_packages.load_container_packages(
        neo4j_session,
        transformed_packages,
        TEST_ORG_URL,
        TEST_UPDATE_TAG,
    )

    # Verify initial count
    assert check_nodes(neo4j_session, "GitHubContainerPackage", ["id"]) == {
        ("123456",),
        ("123457",),
        ("123458",),
    }

    # Act: Load with only one package and new update tag
    new_update_tag = TEST_UPDATE_TAG + 1
    single_package = [tests.data.github.container_packages.GET_CONTAINER_PACKAGES[0]]

    transformed_single = (
        cartography.intel.github.container_packages.transform_container_packages(
            single_package,
            TEST_ORG_URL,
        )
    )

    cartography.intel.github.container_packages.load_container_packages(
        neo4j_session,
        transformed_single,
        TEST_ORG_URL,
        new_update_tag,
    )

    # Run cleanup
    common_job_parameters = {
        "UPDATE_TAG": new_update_tag,
        "org_url": TEST_ORG_URL,
    }

    cartography.intel.github.container_packages.cleanup_container_packages(
        neo4j_session,
        common_job_parameters,
    )

    # Assert: Only the updated package should remain
    assert check_nodes(neo4j_session, "GitHubContainerPackage", ["id"]) == {
        ("123456",),
    }
