from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.github.repos import _canonicalize_dependency_name
from cartography.intel.github.repos import _extract_version_from_requirements
from cartography.intel.github.repos import _get_repo_collaborators_for_multiple_repos
from cartography.intel.github.repos import _transform_dependency_graph
from cartography.intel.github.repos import load_github_dependencies
from tests.data.github.repos import DEPENDENCY_GRAPH_EMPTY_MANIFESTS
from tests.data.github.repos import DEPENDENCY_GRAPH_NO_DEPENDENCIES
from tests.data.github.repos import DEPENDENCY_GRAPH_WITH_MISSING_FIELDS
from tests.data.github.repos import DEPENDENCY_GRAPH_WITH_MULTIPLE_ECOSYSTEMS


@patch("time.sleep", return_value=None)
@patch("cartography.intel.github.repos._get_repo_collaborators")
@patch("cartography.intel.github.repos.backoff_handler", spec=True)
def test_get_team_users_github_returns_none(
    mock_backoff_handler,
    mock_get_team_collaborators,
    mock_sleep,
):
    """
    This test happens to use 'OUTSIDE' affiliation, but it's irrelevant for the test, it just needs either valid value.
    """
    # Arrange
    repo_data = [
        {
            "name": "repo1",
            "url": "https://github.com/repo1",
            "outsideCollaborators": {"totalCount": 1},
        },
    ]
    mock_repo_collabs = MagicMock()
    # Set up the condition where GitHub returns a None url and None edge as in #1334.
    mock_repo_collabs.nodes = [None]
    mock_repo_collabs.edges = [None]
    mock_get_team_collaborators.return_value = mock_repo_collabs

    # Assert we raise an exception
    with pytest.raises(TypeError):
        _get_repo_collaborators_for_multiple_repos(
            repo_data,
            "OUTSIDE",
            "test-org",
            "https://api.github.com",
            "test-token",
        )

    # Assert that we retry and give up
    assert mock_sleep.call_count == 4
    assert mock_get_team_collaborators.call_count == 5
    assert mock_backoff_handler.call_count == 4


# Tests for dependency graph transformation functions
def test_extract_version_from_requirements_exact_version():
    """Test extracting exact versions without operators."""
    # Arrange & Act & Assert
    assert _extract_version_from_requirements("1.2.3") == "1.2.3"
    assert _extract_version_from_requirements("0.1.0") == "0.1.0"
    assert _extract_version_from_requirements("2.0.0-alpha.1") == "2.0.0-alpha.1"


def test_extract_version_from_requirements_equals_operator():
    """Test extracting versions with == operator."""
    # Arrange & Act & Assert
    assert _extract_version_from_requirements("==1.2.3") == "1.2.3"
    assert _extract_version_from_requirements("==0.1.0,<2.0") == "0.1.0"
    assert _extract_version_from_requirements("== 1.2.3 ") == "1.2.3"


def test_extract_version_from_requirements_complex_constraints():
    """Test that complex version constraints return None."""
    # Arrange & Act & Assert
    assert _extract_version_from_requirements(">=1.0.0") is None
    assert _extract_version_from_requirements("^1.2.3") is None
    assert _extract_version_from_requirements("~1.2.0") is None
    assert _extract_version_from_requirements(">=1.0,<2.0") is None
    assert _extract_version_from_requirements("*") is None


def test_extract_version_from_requirements_empty_inputs():
    """Test handling empty or None inputs."""
    # Arrange & Act & Assert
    assert _extract_version_from_requirements("") is None
    assert _extract_version_from_requirements(None) is None
    assert _extract_version_from_requirements("   ") is None


def test_canonicalize_dependency_name_python_packages():
    """Test canonicalization for Python packages."""
    # Arrange & Act & Assert
    assert _canonicalize_dependency_name("Django", "PIP") == "django"
    assert _canonicalize_dependency_name("Flask-Login", "PIP") == "flask-login"
    assert _canonicalize_dependency_name("Pillow_SIMD", "CONDA") == "pillow-simd"


def test_canonicalize_dependency_name_other_ecosystems():
    """Test canonicalization for non-Python ecosystems."""
    # Arrange & Act & Assert
    assert _canonicalize_dependency_name("React", "NPM") == "react"
    assert _canonicalize_dependency_name("Spring-Boot", "MAVEN") == "spring-boot"
    assert _canonicalize_dependency_name("SOME_PACKAGE", "GO") == "some_package"


def test_canonicalize_dependency_name_edge_cases():
    """Test canonicalization edge cases."""
    # Arrange & Act & Assert
    assert _canonicalize_dependency_name("", "NPM") == ""
    assert _canonicalize_dependency_name("Test", "") == "test"
    assert _canonicalize_dependency_name("Test", None) == "test"


def test_transform_dependency_graph_multiple_ecosystems():
    """Test successful transformation of dependency graph data with multiple ecosystems."""
    # Arrange
    repo_url = "https://github.com/test/repo"
    output_list = []

    # Act
    _transform_dependency_graph(
        DEPENDENCY_GRAPH_WITH_MULTIPLE_ECOSYSTEMS, repo_url, output_list
    )

    # Assert
    assert len(output_list) == 4

    # Check NPM dependency with exact version
    react_dep = next(dep for dep in output_list if dep["original_name"] == "react")
    assert react_dep["id"] == "react|18.2.0"
    assert react_dep["name"] == "react"
    assert react_dep["version"] == "18.2.0"
    assert react_dep["requirements"] == "18.2.0"
    assert react_dep["ecosystem"] == "npm"
    assert react_dep["package_manager"] == "NPM"
    assert react_dep["manifest_path"] == "/package.json"
    assert react_dep["repo_url"] == repo_url

    # Check NPM dependency with complex version
    lodash_dep = next(dep for dep in output_list if dep["original_name"] == "lodash")
    assert lodash_dep["id"] == "lodash"  # No pinned version
    assert lodash_dep["name"] == "lodash"
    assert lodash_dep["version"] is None
    assert lodash_dep["requirements"] == "^4.17.21"
    assert lodash_dep["ecosystem"] == "npm"

    # Check Python dependency
    django_dep = next(dep for dep in output_list if dep["original_name"] == "Django")
    assert django_dep["id"] == "django|4.2.0"
    assert django_dep["name"] == "django"  # Canonicalized
    assert django_dep["version"] == "4.2.0"
    assert django_dep["ecosystem"] == "pip"
    assert django_dep["manifest_path"] == "/requirements.txt"

    # Check Maven dependency
    maven_dep = next(
        dep
        for dep in output_list
        if dep["original_name"] == "org.springframework:spring-core"
    )
    assert maven_dep["id"] == "org.springframework:spring-core|5.3.21"
    assert maven_dep["name"] == "org.springframework:spring-core"
    assert maven_dep["version"] == "5.3.21"
    assert maven_dep["ecosystem"] == "maven"
    assert maven_dep["manifest_path"] == "/pom.xml"


def test_transform_dependency_graph_empty_manifests():
    """Test handling of empty or missing manifest data."""
    # Arrange
    repo_url = "https://github.com/test/repo"
    output_list = []

    # Act & Assert - None input
    _transform_dependency_graph(None, repo_url, output_list)
    assert len(output_list) == 0

    # Act & Assert - Empty nodes
    _transform_dependency_graph(DEPENDENCY_GRAPH_EMPTY_MANIFESTS, repo_url, output_list)
    assert len(output_list) == 0

    # Act & Assert - Missing nodes
    _transform_dependency_graph({}, repo_url, output_list)
    assert len(output_list) == 0


def test_transform_dependency_graph_missing_fields():
    """Test handling of missing or malformed dependency fields."""
    # Arrange
    repo_url = "https://github.com/test/repo"
    output_list = []

    # Act
    _transform_dependency_graph(
        DEPENDENCY_GRAPH_WITH_MISSING_FIELDS, repo_url, output_list
    )

    # Assert
    assert len(output_list) == 3  # Should skip the one without packageName

    # Check valid package
    valid_dep = next(
        dep for dep in output_list if dep["original_name"] == "valid-package"
    )
    assert valid_dep["requirements"] is None
    assert valid_dep["version"] is None
    assert valid_dep["ecosystem"] == "npm"

    # Check package with empty requirements
    empty_req_dep = next(
        dep for dep in output_list if dep["original_name"] == "another-package"
    )
    assert empty_req_dep["requirements"] is None
    assert empty_req_dep["ecosystem"] == "unknown"

    # Check package with missing blobPath
    test_dep = next(
        dep for dep in output_list if dep["original_name"] == "test-package"
    )
    assert test_dep["manifest_path"] == ""
    assert test_dep["ecosystem"] == "unknown"


def test_transform_dependency_graph_no_dependencies():
    """Test handling manifests with no dependencies."""
    # Arrange
    repo_url = "https://github.com/test/repo"
    output_list = []

    # Act
    _transform_dependency_graph(DEPENDENCY_GRAPH_NO_DEPENDENCIES, repo_url, output_list)

    # Assert
    assert len(output_list) == 0


# Tests for load_github_dependencies function
def test_load_github_dependencies_success():
    """Test successful loading of GitHub dependencies into Neo4j."""
    # Arrange
    mock_session = MagicMock()
    update_tag = 123456789
    dependencies = [
        {
            "id": "react|18.2.0",
            "name": "react",
            "original_name": "react",
            "version": "18.2.0",
            "requirements": "18.2.0",
            "ecosystem": "npm",
            "package_manager": "NPM",
            "manifest_path": "/package.json",
            "repo_url": "https://github.com/test/repo",
        },
        {
            "id": "django|4.2.0",
            "name": "django",
            "original_name": "Django",
            "version": "4.2.0",
            "requirements": "==4.2.0",
            "ecosystem": "pip",
            "package_manager": "PIP",
            "manifest_path": "/requirements.txt",
            "repo_url": "https://github.com/test/repo",
        },
    ]

    # Act
    load_github_dependencies(mock_session, update_tag, dependencies)

    # Assert
    assert mock_session.run.call_count == 1
    call_args = mock_session.run.call_args

    # Check that the query was called with correct parameters
    assert "UNWIND $Dependencies AS dep" in call_args[0][0]
    assert "MERGE (lib:Dependency{id: dep.id})" in call_args[0][0]
    assert "MERGE (repo)-[r:REQUIRES]->(lib)" in call_args[0][0]

    # Check the parameters
    assert call_args[1]["Dependencies"] == dependencies
    assert call_args[1]["UpdateTag"] == update_tag


def test_load_github_dependencies_empty_list():
    """Test loading empty dependencies list."""
    # Arrange
    mock_session = MagicMock()
    update_tag = 123456789
    dependencies = []

    # Act
    load_github_dependencies(mock_session, update_tag, dependencies)

    # Assert
    assert mock_session.run.call_count == 1
    call_args = mock_session.run.call_args
    assert call_args[1]["Dependencies"] == []
    assert call_args[1]["UpdateTag"] == update_tag


def test_load_github_dependencies_query_structure():
    """Test that the Cypher query has the correct structure for dependencies."""
    # Arrange
    mock_session = MagicMock()
    update_tag = 123456789
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
        },
    ]

    # Act
    load_github_dependencies(mock_session, update_tag, dependencies)

    # Assert
    call_args = mock_session.run.call_args
    query = call_args[0][0]

    # Check key parts of the query
    assert "MERGE (lib:Dependency{id: dep.id})" in query
    assert "lib.name = dep.name" in query
    assert "lib.original_name = dep.original_name" in query
    assert "lib.version = dep.version" in query
    assert "lib.ecosystem = dep.ecosystem" in query
    assert "lib.package_manager = dep.package_manager" in query
    assert "MATCH (repo:GitHubRepository{id: dep.repo_url})" in query
    assert "r.requirements = dep.requirements" in query
    assert "r.manifest_path = dep.manifest_path" in query
