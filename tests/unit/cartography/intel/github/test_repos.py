from cartography.intel.github.repos import _create_git_url_from_ssh_url
from cartography.intel.github.repos import _transform_dependency_graph
from cartography.intel.github.repos import _transform_dependency_manifests
from cartography.intel.github.repos import transform
from tests.data.github.repos import DEPENDENCY_GRAPH_WITH_MULTIPLE_ECOSYSTEMS
from tests.data.github.repos import GET_REPOS

TEST_UPDATE_TAG = 123456789


def test_transform_dependency_manifests_converts_to_expected_format():
    """
    Test that the manifest transformation function correctly processes GitHub API data
    into the format expected for loading manifest nodes into the database.
    """
    # Arrange
    repo_url = "https://github.com/test-org/test-repo"
    output_list = []

    # Act
    _transform_dependency_manifests(
        DEPENDENCY_GRAPH_WITH_MULTIPLE_ECOSYSTEMS, repo_url, output_list
    )

    # Assert: Check that 3 manifests were transformed
    assert len(output_list) == 3

    # Assert: Check that expected manifest IDs are present
    manifest_ids = {manifest["id"] for manifest in output_list}
    expected_ids = {
        "https://github.com/test-org/test-repo#/package.json",
        "https://github.com/test-org/test-repo#/requirements.txt",
        "https://github.com/test-org/test-repo#/pom.xml",
    }
    assert manifest_ids == expected_ids

    # Assert: Check that a specific manifest has expected properties
    package_json_manifest = next(
        manifest for manifest in output_list if manifest["filename"] == "package.json"
    )
    assert (
        package_json_manifest["id"]
        == "https://github.com/test-org/test-repo#/package.json"
    )
    assert package_json_manifest["blob_path"] == "/package.json"
    assert package_json_manifest["filename"] == "package.json"
    assert package_json_manifest["dependencies_count"] == 2  # react and lodash
    assert package_json_manifest["repo_url"] == repo_url

    # Assert: Check requirements.txt manifest
    requirements_manifest = next(
        manifest
        for manifest in output_list
        if manifest["filename"] == "requirements.txt"
    )
    assert requirements_manifest["dependencies_count"] == 1  # Django
    assert requirements_manifest["blob_path"] == "/requirements.txt"

    # Assert: Check pom.xml manifest
    pom_manifest = next(
        manifest for manifest in output_list if manifest["filename"] == "pom.xml"
    )
    assert pom_manifest["dependencies_count"] == 1  # spring-core
    assert pom_manifest["blob_path"] == "/pom.xml"


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

    # Assert: Check that expected dependency IDs are present (now using raw requirements)
    dependency_ids = {dep["id"] for dep in output_list}
    expected_ids = {
        "react|18.2.0",
        "lodash",
        "django|= 4.2.0",
        "org.springframework:spring-core|5.3.21",
    }
    assert dependency_ids == expected_ids

    # Assert: Check that a specific dependency has expected properties
    react_dep = next(dep for dep in output_list if dep["original_name"] == "react")
    assert react_dep["id"] == "react|18.2.0"
    assert react_dep["name"] == "react"
    assert react_dep["requirements"] == "18.2.0"
    assert react_dep["ecosystem"] == "npm"
    assert react_dep["package_manager"] == "NPM"
    assert react_dep["manifest_path"] == "/package.json"
    assert react_dep["repo_url"] == repo_url
    assert react_dep["manifest_file"] == "package.json"


def test_create_git_url_from_ssh_url():
    """
    Test that _create_git_url_from_ssh_url correctly converts SSH URLs to git:// format.
    """
    # Arrange
    ssh_url = "git@github.com:cartography-cncf/cartography.git"
    expected_result = "git://github.com/cartography-cncf/cartography.git"

    # Act
    result = _create_git_url_from_ssh_url(ssh_url)

    # Assert
    assert result == expected_result

    # Test with nested path (monorepo case)
    ssh_url_nested = "git@github.com:user/nested/path/repo.git"
    expected_nested = "git://github.com/user/nested/path/repo.git"
    result_nested = _create_git_url_from_ssh_url(ssh_url_nested)
    assert result_nested == expected_nested


def test_transform_skips_null_repository_entries():
    repo_with_collab_counts = GET_REPOS[0]

    result = transform(
        [None, repo_with_collab_counts],
        {repo_with_collab_counts["url"]: []},
        {repo_with_collab_counts["url"]: []},
    )

    assert len(result["repos"]) == 1
    assert result["repos"][0]["id"] == repo_with_collab_counts["url"]
