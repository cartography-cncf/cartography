from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gitlab.repositories import _extract_groups_from_repositories
from cartography.intel.gitlab.repositories import _fetch_languages_for_repo


def test_extract_groups_from_repositories():
    """Test that groups are correctly extracted from repository data"""
    # Arrange
    repositories = [
        {
            "id": "https://gitlab.com/projects/1",
            "name": "repo1",
            "namespace_id": "https://gitlab.com/groups/10",
            "namespace_numeric_id": 10,
            "namespace_kind": "group",
            "namespace_name": "Engineering",
            "namespace_path": "engineering",
            "namespace_full_path": "engineering",
            "web_url": "https://gitlab.com/engineering/repo1",
            "visibility": "private",
        },
        {
            "id": "https://gitlab.com/projects/2",
            "name": "repo2",
            "namespace_id": "https://gitlab.com/groups/10",
            "namespace_numeric_id": 10,
            "namespace_kind": "group",
            "namespace_name": "Engineering",
            "namespace_path": "engineering",
            "namespace_full_path": "engineering",
            "web_url": "https://gitlab.com/engineering/repo2",
            "visibility": "internal",
        },
        {
            "id": "https://gitlab.com/projects/3",
            "name": "repo3",
            "namespace_id": "https://gitlab.com/groups/20",
            "namespace_numeric_id": 20,
            "namespace_kind": "group",
            "namespace_name": "Data",
            "namespace_path": "data",
            "namespace_full_path": "data",
            "web_url": "https://gitlab.com/data/repo3",
            "visibility": "public",
        },
        {
            "id": "https://gitlab.com/projects/4",
            "name": "user-repo",
            "namespace_id": "https://gitlab.com/users/30",
            "namespace_numeric_id": 30,
            "namespace_kind": "user",  # User namespace, should be filtered out
            "namespace_name": "jdoe",
            "namespace_path": "jdoe",
            "namespace_full_path": "jdoe",
            "web_url": "https://gitlab.com/jdoe/user-repo",
            "visibility": "private",
        },
    ]

    # Act
    groups = _extract_groups_from_repositories(repositories)

    # Assert
    # Should only extract 2 groups (10 and 20), not the user namespace (30)
    assert len(groups) == 2

    # Check group IDs are unique and correctly formatted
    group_ids = {g["id"] for g in groups}
    assert group_ids == {
        "https://gitlab.com/groups/10",
        "https://gitlab.com/groups/20",
    }

    # Check that groups have all required fields
    eng_group = next(g for g in groups if g["numeric_id"] == 10)
    assert eng_group["name"] == "Engineering"
    assert eng_group["path"] == "engineering"
    assert eng_group["full_path"] == "engineering"
    assert "web_url" in eng_group


def test_extract_groups_handles_empty_list():
    """Test that extracting groups from an empty list returns empty list"""
    # Arrange
    repositories = []

    # Act
    groups = _extract_groups_from_repositories(repositories)

    # Assert
    assert groups == []


def test_extract_groups_handles_repos_without_namespaces():
    """Test that repos without namespace data are handled gracefully"""
    # Arrange
    repositories = [
        {
            "id": "https://gitlab.com/projects/1",
            "name": "repo1",
            "namespace_id": None,
            "namespace_kind": None,
            "web_url": "https://gitlab.com/repo1",
        },
    ]

    # Act
    groups = _extract_groups_from_repositories(repositories)

    # Assert
    assert groups == []


def test_fetch_languages_for_repo_success():
    """Test successful language fetching for a repository"""
    # Arrange
    mock_client = MagicMock()
    mock_project = MagicMock()
    mock_project.languages.return_value = {
        "Python": 65.5,
        "JavaScript": 34.5,
    }
    mock_client.projects.get.return_value = mock_project

    repo_unique_id = "https://gitlab.com/projects/123"
    repo_numeric_id = 123

    # Act
    result = _fetch_languages_for_repo(mock_client, repo_unique_id, repo_numeric_id)

    # Assert
    assert len(result) == 2

    # Check Python mapping
    python_mapping = next(m for m in result if m["language_name"] == "Python")
    assert python_mapping["repo_id"] == repo_unique_id
    assert python_mapping["percentage"] == 65.5

    # Check JavaScript mapping
    js_mapping = next(m for m in result if m["language_name"] == "JavaScript")
    assert js_mapping["repo_id"] == repo_unique_id
    assert js_mapping["percentage"] == 34.5

    # Verify API was called with numeric ID
    mock_client.projects.get.assert_called_once_with(repo_numeric_id)


def test_fetch_languages_for_repo_handles_empty_languages():
    """Test handling of repositories with no language data"""
    # Arrange
    mock_client = MagicMock()
    mock_project = MagicMock()
    mock_project.languages.return_value = {}  # Empty dict for repos with no code
    mock_client.projects.get.return_value = mock_project

    repo_unique_id = "https://gitlab.com/projects/123"
    repo_numeric_id = 123

    # Act
    result = _fetch_languages_for_repo(mock_client, repo_unique_id, repo_numeric_id)

    # Assert
    assert result == []


def test_fetch_languages_for_repo_handles_api_error():
    """Test that API errors are handled gracefully"""
    # Arrange
    mock_client = MagicMock()
    mock_client.projects.get.side_effect = Exception("API Error")

    repo_unique_id = "https://gitlab.com/projects/123"
    repo_numeric_id = 123

    # Act
    result = _fetch_languages_for_repo(mock_client, repo_unique_id, repo_numeric_id)

    # Assert
    assert result == []  # Should return empty list on error, not raise


def test_extract_groups_deduplicates_by_id():
    """Test that duplicate group IDs are properly deduplicated"""
    # Arrange
    repositories = [
        {
            "id": "https://gitlab.com/projects/1",
            "name": "repo1",
            "namespace_id": "https://gitlab.com/groups/10",
            "namespace_numeric_id": 10,
            "namespace_kind": "group",
            "namespace_name": "Engineering",
            "namespace_path": "engineering",
            "namespace_full_path": "engineering",
            "web_url": "https://gitlab.com/engineering/repo1",
            "visibility": "private",
        },
        {
            "id": "https://gitlab.com/projects/2",
            "name": "repo2",
            "namespace_id": "https://gitlab.com/groups/10",  # Same group
            "namespace_numeric_id": 10,
            "namespace_kind": "group",
            "namespace_name": "Engineering",
            "namespace_path": "engineering",
            "namespace_full_path": "engineering",
            "web_url": "https://gitlab.com/engineering/repo2",
            "visibility": "private",
        },
    ]

    # Act
    groups = _extract_groups_from_repositories(repositories)

    # Assert
    assert len(groups) == 1  # Should deduplicate
    assert groups[0]["id"] == "https://gitlab.com/groups/10"
