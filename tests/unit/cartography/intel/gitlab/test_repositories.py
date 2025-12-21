from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gitlab.repositories import _extract_groups_from_repositories
from cartography.intel.gitlab.repositories import _fetch_languages_for_repo
from cartography.intel.gitlab.repositories import _get_repository_languages
from cartography.intel.gitlab.repositories import get_gitlab_repositories


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


@patch("gitlab.Gitlab")
def test_get_gitlab_repositories_transforms_project_objects(mock_gitlab_class):
    """Test that get_gitlab_repositories correctly transforms GitLab project objects into our data structure"""
    # Arrange
    mock_client = MagicMock()
    mock_gitlab_class.return_value = mock_client

    # Create a mock project that mimics the python-gitlab Project object
    mock_project = MagicMock()
    mock_project.id = 12345
    mock_project.name = "test-project"
    mock_project.path = "test-project"
    mock_project.path_with_namespace = "engineering/test-project"
    mock_project.web_url = "https://gitlab.example.com/engineering/test-project"
    mock_project.http_url_to_repo = (
        "https://gitlab.example.com/engineering/test-project.git"
    )
    mock_project.ssh_url_to_repo = "git@gitlab.example.com:engineering/test-project.git"
    mock_project.description = "Test description"
    mock_project.visibility = "private"
    mock_project.archived = False
    mock_project.default_branch = "main"
    mock_project.star_count = 5
    mock_project.forks_count = 2
    mock_project.open_issues_count = 3
    mock_project.created_at = "2024-01-01T00:00:00Z"
    mock_project.last_activity_at = "2024-12-01T00:00:00Z"
    mock_project.issues_enabled = True
    mock_project.merge_requests_enabled = True
    mock_project.wiki_enabled = False
    mock_project.snippets_enabled = True
    mock_project.container_registry_enabled = True
    mock_project.empty_repo = False

    # Mock namespace
    mock_project.namespace = {
        "id": 100,
        "kind": "group",
        "name": "Engineering",
        "path": "engineering",
        "full_path": "engineering",
    }

    mock_client.projects.list.return_value = [mock_project]

    # Act
    repositories = get_gitlab_repositories("https://gitlab.example.com", "test-token")

    # Assert
    assert len(repositories) == 1
    repo = repositories[0]

    # Check URL-based unique ID generation
    assert repo["id"] == "https://gitlab.example.com/projects/12345"
    assert repo["numeric_id"] == 12345

    # Check field extraction
    assert repo["name"] == "test-project"
    assert repo["path_with_namespace"] == "engineering/test-project"
    assert repo["visibility"] == "private"
    assert repo["archived"] is False
    assert repo["star_count"] == 5

    # Check namespace transformation
    assert repo["namespace_id"] == "https://gitlab.example.com/groups/100"
    assert repo["namespace_numeric_id"] == 100
    assert repo["namespace_kind"] == "group"
    assert repo["namespace_name"] == "Engineering"


@patch("gitlab.Gitlab")
def test_get_gitlab_repositories_handles_missing_optional_fields(mock_gitlab_class):
    """Test that optional fields are handled gracefully when missing from API"""
    # Arrange
    mock_client = MagicMock()
    mock_gitlab_class.return_value = mock_client

    # Create a minimal mock project with only required fields
    mock_project = MagicMock()
    mock_project.id = 999
    mock_project.name = "minimal-project"
    mock_project.path = "minimal-project"
    mock_project.path_with_namespace = "user/minimal-project"
    mock_project.web_url = "https://gitlab.example.com/user/minimal-project"
    mock_project.http_url_to_repo = (
        "https://gitlab.example.com/user/minimal-project.git"
    )
    mock_project.ssh_url_to_repo = "git@gitlab.example.com:user/minimal-project.git"
    mock_project.description = None  # Can be None
    mock_project.visibility = "internal"
    mock_project.archived = False
    mock_project.created_at = "2024-01-01T00:00:00Z"
    mock_project.last_activity_at = "2024-12-01T00:00:00Z"
    mock_project.issues_enabled = True
    mock_project.merge_requests_enabled = True
    mock_project.wiki_enabled = True
    mock_project.snippets_enabled = True
    mock_project.namespace = {
        "id": 200,
        "kind": "user",
        "name": "johndoe",
        "path": "johndoe",
        "full_path": "johndoe",
    }

    # Simulate missing optional attributes (no hasattr check would find these)
    # Delete attributes that might not exist on all projects
    del mock_project.readme_url
    del mock_project.default_branch
    del mock_project.star_count
    del mock_project.forks_count
    del mock_project.open_issues_count
    del mock_project.container_registry_enabled
    del mock_project.empty_repo

    mock_client.projects.list.return_value = [mock_project]

    # Act
    repositories = get_gitlab_repositories("https://gitlab.example.com", "test-token")

    # Assert
    assert len(repositories) == 1
    repo = repositories[0]

    # Check that missing optional fields default correctly
    assert repo["readme_url"] is None
    assert repo["default_branch"] is None
    assert repo["star_count"] == 0  # Defaults to 0
    assert repo["forks_count"] == 0
    assert repo["open_issues_count"] == 0
    assert repo["container_registry_enabled"] is False
    assert repo["empty_repo"] is False
    assert repo["description"] == ""  # None becomes ""


@patch("gitlab.Gitlab")
def test_get_gitlab_repositories_normalizes_urls(mock_gitlab_class):
    """Test that GitLab URLs are normalized for consistent ID generation"""
    # Arrange
    mock_client = MagicMock()
    mock_gitlab_class.return_value = mock_client

    mock_project = MagicMock()
    mock_project.id = 555
    mock_project.name = "url-test"
    mock_project.path = "url-test"
    mock_project.path_with_namespace = "group/url-test"
    mock_project.web_url = "https://gitlab.example.com/group/url-test"
    mock_project.http_url_to_repo = "https://gitlab.example.com/group/url-test.git"
    mock_project.ssh_url_to_repo = "git@gitlab.example.com:group/url-test.git"
    mock_project.description = ""
    mock_project.visibility = "private"
    mock_project.archived = False
    mock_project.created_at = "2024-01-01T00:00:00Z"
    mock_project.last_activity_at = "2024-12-01T00:00:00Z"
    mock_project.issues_enabled = True
    mock_project.merge_requests_enabled = True
    mock_project.wiki_enabled = True
    mock_project.snippets_enabled = True
    mock_project.namespace = {
        "id": 10,
        "kind": "group",
        "name": "Group",
        "path": "group",
        "full_path": "group",
    }

    mock_client.projects.list.return_value = [mock_project]

    # Act
    repositories = get_gitlab_repositories(
        "https://gitlab.example.com/", "test-token"
    )  # Note trailing slash

    # Assert: Trailing slash should be stripped for consistent IDs
    assert repositories[0]["id"] == "https://gitlab.example.com/projects/555"
    assert not repositories[0]["id"].startswith("https://gitlab.example.com//")


def test_get_gitlab_repositories_validates_credentials():
    """Test that missing credentials raises ValueError"""
    # Act & Assert: Missing URL
    try:
        get_gitlab_repositories("", "token")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "GitLab URL and token are required" in str(e)

    # Act & Assert: Missing token
    try:
        get_gitlab_repositories("https://gitlab.com", "")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "GitLab URL and token are required" in str(e)

    # Act & Assert: Both None
    try:
        get_gitlab_repositories(None, None)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "GitLab URL and token are required" in str(e)


def test_get_repository_languages_with_parallel_execution():
    """Test that _get_repository_languages uses parallel execution correctly"""
    # Arrange
    repositories = [
        {"id": f"https://gitlab.com/projects/{i}", "numeric_id": i}
        for i in range(1, 21)
    ]  # 20 repos

    # Mock the language fetch to return predictable data
    def mock_fetch_languages(client, unique_id, numeric_id):
        return [{"repo_id": unique_id, "language_name": "Python", "percentage": 100.0}]

    # Act
    with patch(
        "cartography.intel.gitlab.repositories._fetch_languages_for_repo",
        side_effect=mock_fetch_languages,
    ):
        with patch("gitlab.Gitlab") as mock_gitlab:
            mock_gitlab.return_value = MagicMock()
            language_mappings = _get_repository_languages(
                "https://gitlab.com",
                "token",
                repositories,
                max_workers=5,  # Use 5 workers for test
            )

    # Assert: Should have fetched languages for all 20 repos
    assert len(language_mappings) == 20
    # All should be Python at 100%
    assert all(m["language_name"] == "Python" for m in language_mappings)
    assert all(m["percentage"] == 100.0 for m in language_mappings)


def test_get_repository_languages_handles_errors_gracefully():
    """Test that errors in individual repo language fetching don't stop the entire process"""
    # Arrange
    repositories = [
        {"id": "https://gitlab.com/projects/1", "numeric_id": 1},
        {"id": "https://gitlab.com/projects/2", "numeric_id": 2},
        {"id": "https://gitlab.com/projects/3", "numeric_id": 3},
    ]

    # Mock fetch to fail for repo 2 but succeed for others
    def mock_fetch_languages(client, unique_id, numeric_id):
        if numeric_id == 2:
            raise Exception("API Error for repo 2")
        return [{"repo_id": unique_id, "language_name": "Python", "percentage": 100.0}]

    # Act
    with patch(
        "cartography.intel.gitlab.repositories._fetch_languages_for_repo",
        side_effect=mock_fetch_languages,
    ):
        with patch("gitlab.Gitlab") as mock_gitlab:
            mock_gitlab.return_value = MagicMock()
            language_mappings = _get_repository_languages(
                "https://gitlab.com",
                "token",
                repositories,
                max_workers=2,
            )

    # Assert: Should have languages for repos 1 and 3, but not 2
    assert len(language_mappings) == 2
    repo_ids_with_languages = {m["repo_id"] for m in language_mappings}
    assert "https://gitlab.com/projects/1" in repo_ids_with_languages
    assert "https://gitlab.com/projects/3" in repo_ids_with_languages
    assert "https://gitlab.com/projects/2" not in repo_ids_with_languages
