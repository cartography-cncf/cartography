from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.github.repos import _transform_dependency_graph
from cartography.intel.github.repos import load_github_dependencies
from tests.data.github.repos import DEPENDENCY_GRAPH_WITH_MULTIPLE_ECOSYSTEMS

TEST_UPDATE_TAG = 123456789


def test_transform_dependency_converts_to_expected_format():
    """
    Test that the dependency transformation function correctly processes GitHub API data
    into the format expected for loading into the database.
    """
    # Arrange
    repo_url = "https://github.com/test-org/test-repo"
    output_list = []

    # Act
    _transform_dependency_graph(
        DEPENDENCY_GRAPH_WITH_MULTIPLE_ECOSYSTEMS, repo_url, output_list
    )

    # Assert: Check that 4 dependencies were transformed
    assert len(output_list) == 4

    # Assert: Check that expected dependency IDs are present
    dependency_ids = {dep["id"] for dep in output_list}
    expected_ids = {
        "react|18.2.0",
        "lodash",
        "django|4.2.0",
        "org.springframework:spring-core|5.3.21",
    }
    assert dependency_ids == expected_ids

    # Assert: Check that a specific dependency has expected properties
    react_dep = next(dep for dep in output_list if dep["original_name"] == "react")
    assert react_dep["id"] == "react|18.2.0"
    assert react_dep["name"] == "react"
    assert react_dep["version"] == "18.2.0"
    assert react_dep["requirements"] == "18.2.0"
    assert react_dep["ecosystem"] == "npm"
    assert react_dep["package_manager"] == "NPM"
    assert react_dep["manifest_path"] == "/package.json"
    assert react_dep["repo_url"] == repo_url


@patch("cartography.intel.github.repos.load_data")
def test_load_github_dependencies_calls_data_model_correctly(mock_load):
    """
    Test that the load function calls the new data model load function with correct parameters.
    """
    # Arrange
    mock_neo4j_session = MagicMock()
    dependencies = [
        {
            "id": "test-package|1.0.0",
            "name": "test-package",
            "original_name": "Test-Package",
            "version": "1.0.0",
            "requirements": "1.0.0",
            "ecosystem": "npm",
            "package_manager": "NPM",
            "manifest_path": "/package.json",
            "repo_url": "https://github.com/test/repo",
        }
    ]

    # Act
    load_github_dependencies(mock_neo4j_session, TEST_UPDATE_TAG, dependencies)

    # Assert: Check that the data model load function was called correctly
    mock_load.assert_called_once()
    call_args = mock_load.call_args

    # Verify the function was called with correct arguments
    assert call_args[0][0] == mock_neo4j_session  # neo4j_session
    # GitHubDependencySchema should be the second argument - check the type
    assert call_args[0][1].__class__.__name__ == "GitHubDependencySchema"

    # The function removes repo_url from each dependency before passing to load_data
    expected_dependencies = [
        {
            "id": "test-package|1.0.0",
            "name": "test-package",
            "original_name": "Test-Package",
            "version": "1.0.0",
            "requirements": "1.0.0",
            "ecosystem": "npm",
            "package_manager": "NPM",
            "manifest_path": "/package.json",
            # Note: repo_url is removed from the dependency object
        }
    ]
    assert (
        call_args[0][2] == expected_dependencies
    )  # dependencies data (without repo_url)

    # Check keyword arguments
    assert call_args[1]["lastupdated"] == TEST_UPDATE_TAG
    assert (
        call_args[1]["repo_url"] == "https://github.com/test/repo"
    )  # repo_url passed as kwarg
