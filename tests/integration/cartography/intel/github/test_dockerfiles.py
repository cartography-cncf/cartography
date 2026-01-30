import json
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.github.dockerfiles
from tests.data.github.dockerfiles import DOCKERFILE_CONTENT
from tests.data.github.dockerfiles import DOCKERFILE_DEV_CONTENT
from tests.data.github.dockerfiles import DOCKERFILE_PROD_CONTENT
from tests.data.github.dockerfiles import FILE_CONTENT_DOCKERFILE
from tests.data.github.dockerfiles import FILE_CONTENT_DOCKERFILE_DEV
from tests.data.github.dockerfiles import FILE_CONTENT_DOCKERFILE_PROD
from tests.data.github.dockerfiles import SEARCH_DOCKERFILES_EMPTY_RESPONSE
from tests.data.github.dockerfiles import SEARCH_DOCKERFILES_ORG_RESPONSE
from tests.data.github.dockerfiles import SEARCH_DOCKERFILES_RESPONSE
from tests.data.github.dockerfiles import TEST_REPOS

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://api.github.com/graphql"


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_search_dockerfiles_in_repo(mock_rest_api):
    """
    Test that search_dockerfiles_in_repo correctly calls the GitHub Code Search API
    and returns the expected results.
    """
    # Arrange
    mock_rest_api.return_value = SEARCH_DOCKERFILES_RESPONSE

    # Act
    results = cartography.intel.github.dockerfiles.search_dockerfiles_in_repo(
        token="test_token",
        owner="testorg",
        repo="testrepo",
        base_url="https://api.github.com",
    )

    # Assert
    mock_rest_api.assert_called_once_with(
        "/search/code",
        "test_token",
        "https://api.github.com",
        {"q": "filename:dockerfile repo:testorg/testrepo", "per_page": 100},
    )
    assert len(results) == 3
    assert results[0]["path"] == "Dockerfile"
    assert results[1]["path"] == "docker/Dockerfile.dev"
    assert results[2]["path"] == "deploy/production.dockerfile"


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_search_dockerfiles_in_repo_empty(mock_rest_api):
    """
    Test that search_dockerfiles_in_repo returns empty list when no Dockerfiles found.
    """
    # Arrange
    mock_rest_api.return_value = SEARCH_DOCKERFILES_EMPTY_RESPONSE

    # Act
    results = cartography.intel.github.dockerfiles.search_dockerfiles_in_repo(
        token="test_token",
        owner="testorg",
        repo="empty-repo",
        base_url="https://api.github.com",
    )

    # Assert
    assert results == []


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_search_dockerfiles_in_org(mock_rest_api):
    """
    Test that search_dockerfiles_in_org correctly calls the GitHub Code Search API
    with org-wide query and returns the expected results.
    """
    # Arrange
    mock_rest_api.return_value = SEARCH_DOCKERFILES_ORG_RESPONSE

    # Act
    results = cartography.intel.github.dockerfiles.search_dockerfiles_in_org(
        token="test_token",
        org="testorg",
        base_url="https://api.github.com",
    )

    # Assert
    mock_rest_api.assert_called_once_with(
        "/search/code",
        "test_token",
        "https://api.github.com",
        {"q": "filename:dockerfile org:testorg", "per_page": 100, "page": 1},
    )
    assert len(results) == 3
    assert results[0]["path"] == "Dockerfile"
    assert results[0]["repository"]["full_name"] == "testorg/testrepo"


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_search_dockerfiles_in_org_with_pagination(mock_rest_api):
    """
    Test that search_dockerfiles_in_org handles pagination correctly.
    """
    # Arrange - simulate 2 pages of results
    page1_response = {
        "total_count": 150,
        "incomplete_results": False,
        "items": SEARCH_DOCKERFILES_ORG_RESPONSE["items"],  # 3 items, simulate 100
    }
    page2_response = {
        "total_count": 150,
        "incomplete_results": False,
        "items": [SEARCH_DOCKERFILES_ORG_RESPONSE["items"][0]],  # 1 more item
    }
    mock_rest_api.side_effect = [page1_response, page2_response]

    # Act
    results = cartography.intel.github.dockerfiles.search_dockerfiles_in_org(
        token="test_token",
        org="testorg",
        base_url="https://api.github.com",
    )

    # Assert - should have made 2 API calls (pages stop when items < 100)
    assert mock_rest_api.call_count == 2
    assert len(results) == 4  # 3 + 1 items


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_search_dockerfiles_in_org_handles_error(mock_rest_api):
    """
    Test that search_dockerfiles_in_org handles HTTP errors gracefully.
    """
    import requests

    # Arrange - simulate a 403 rate limit error
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_rest_api.side_effect = requests.exceptions.HTTPError(response=mock_response)

    # Act
    results = cartography.intel.github.dockerfiles.search_dockerfiles_in_org(
        token="test_token",
        org="testorg",
        base_url="https://api.github.com",
    )

    # Assert - should return empty list, not raise exception
    assert results == []


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_get_file_content(mock_rest_api):
    """
    Test that get_file_content correctly downloads and decodes file content.
    """
    # Arrange
    mock_rest_api.return_value = FILE_CONTENT_DOCKERFILE

    # Act
    content = cartography.intel.github.dockerfiles.get_file_content(
        token="test_token",
        owner="testorg",
        repo="testrepo",
        path="Dockerfile",
        base_url="https://api.github.com",
    )

    # Assert
    mock_rest_api.assert_called_once_with(
        "/repos/testorg/testrepo/contents/Dockerfile",
        "test_token",
        "https://api.github.com",
        {"ref": "HEAD"},
    )
    assert content == DOCKERFILE_CONTENT


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_get_dockerfiles_for_repos_with_org_search(mock_rest_api):
    """
    Test that get_dockerfiles_for_repos uses org-wide search when org is specified.
    """

    # Arrange
    def mock_api_response(endpoint, token, base_url, params=None):
        if "/search/code" in endpoint:
            # Org-wide search
            if "org:testorg" in params.get("q", ""):
                return SEARCH_DOCKERFILES_ORG_RESPONSE
            return SEARCH_DOCKERFILES_EMPTY_RESPONSE
        elif "/contents/Dockerfile" in endpoint and "Dockerfile.dev" not in endpoint:
            return FILE_CONTENT_DOCKERFILE
        elif "/contents/docker/Dockerfile.dev" in endpoint:
            return FILE_CONTENT_DOCKERFILE_DEV
        elif "/contents/deploy/production.dockerfile" in endpoint:
            return FILE_CONTENT_DOCKERFILE_PROD
        return {}

    mock_rest_api.side_effect = mock_api_response

    # Act
    results = cartography.intel.github.dockerfiles.get_dockerfiles_for_repos(
        token="test_token",
        repos=TEST_REPOS,
        base_url="https://api.github.com",
        org="testorg",
    )

    # Assert
    assert len(results) == 3

    # Check first Dockerfile
    dockerfile = next(r for r in results if r["path"] == "Dockerfile")
    assert dockerfile["repo_name"] == "testorg/testrepo"
    assert dockerfile["repo_url"] == "https://github.com/testorg/testrepo"
    assert dockerfile["content"] == DOCKERFILE_CONTENT

    # Check Dockerfile.dev
    dockerfile_dev = next(r for r in results if r["path"] == "docker/Dockerfile.dev")
    assert dockerfile_dev["content"] == DOCKERFILE_DEV_CONTENT

    # Check production.dockerfile
    dockerfile_prod = next(
        r for r in results if r["path"] == "deploy/production.dockerfile"
    )
    assert dockerfile_prod["content"] == DOCKERFILE_PROD_CONTENT


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_get_dockerfiles_for_repos_infers_org(mock_rest_api):
    """
    Test that get_dockerfiles_for_repos infers org from repos when all are from same org.
    """

    # Arrange
    def mock_api_response(endpoint, token, base_url, params=None):
        if "/search/code" in endpoint:
            # Should use org-wide search since all repos are from testorg
            if "org:testorg" in params.get("q", ""):
                return SEARCH_DOCKERFILES_ORG_RESPONSE
            return SEARCH_DOCKERFILES_EMPTY_RESPONSE
        elif "/contents/Dockerfile" in endpoint and "Dockerfile.dev" not in endpoint:
            return FILE_CONTENT_DOCKERFILE
        elif "/contents/docker/Dockerfile.dev" in endpoint:
            return FILE_CONTENT_DOCKERFILE_DEV
        elif "/contents/deploy/production.dockerfile" in endpoint:
            return FILE_CONTENT_DOCKERFILE_PROD
        return {}

    mock_rest_api.side_effect = mock_api_response

    # Act - no org specified, should be inferred
    results = cartography.intel.github.dockerfiles.get_dockerfiles_for_repos(
        token="test_token",
        repos=TEST_REPOS,
        base_url="https://api.github.com",
    )

    # Assert - should still work using inferred org
    assert len(results) == 3


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_get_dockerfiles_for_repos_fallback_to_per_repo(mock_rest_api):
    """
    Test that get_dockerfiles_for_repos falls back to per-repo search
    when repos are from multiple orgs.
    """

    # Arrange - repos from two different orgs
    mixed_repos = [
        {
            "name": "testrepo",
            "nameWithOwner": "testorg/testrepo",
            "url": "https://github.com/testorg/testrepo",
            "owner": {"login": "testorg"},
        },
        {
            "name": "otherrepo",
            "nameWithOwner": "otherorg/otherrepo",
            "url": "https://github.com/otherorg/otherrepo",
            "owner": {"login": "otherorg"},
        },
    ]

    def mock_api_response(endpoint, token, base_url, params=None):
        if "/search/code" in endpoint:
            # Per-repo searches
            if "repo:testorg/testrepo" in params.get("q", ""):
                return {
                    "total_count": 1,
                    "items": [SEARCH_DOCKERFILES_RESPONSE["items"][0]],
                }
            if "repo:otherorg/otherrepo" in params.get("q", ""):
                return SEARCH_DOCKERFILES_EMPTY_RESPONSE
            return SEARCH_DOCKERFILES_EMPTY_RESPONSE
        elif "/contents/Dockerfile" in endpoint:
            return FILE_CONTENT_DOCKERFILE
        return {}

    mock_rest_api.side_effect = mock_api_response

    # Act
    results = cartography.intel.github.dockerfiles.get_dockerfiles_for_repos(
        token="test_token",
        repos=mixed_repos,
        base_url="https://api.github.com",
    )

    # Assert - should have used per-repo search and found 1 Dockerfile
    assert len(results) == 1
    assert results[0]["repo_name"] == "testorg/testrepo"


def test_dockerfile_sync_result_to_tempfile():
    """
    Test that DockerfileSyncResult.to_tempfile() context manager creates
    a valid JSON file and cleans it up on exit.
    """
    # Arrange
    test_dockerfiles = [
        {
            "repo_url": "https://github.com/test/repo",
            "repo_name": "test/repo",
            "path": "Dockerfile",
            "content": "FROM python:3.11",
        }
    ]
    result = cartography.intel.github.dockerfiles.DockerfileSyncResult(
        dockerfiles=test_dockerfiles,
    )

    # Act & Assert - file exists inside context manager
    with result.to_tempfile() as temp_path:
        assert temp_path.exists()
        assert temp_path.suffix == ".json"
        assert "github_dockerfiles_" in temp_path.name

        with open(temp_path) as f:
            loaded_data = json.load(f)

        assert "dockerfiles" in loaded_data
        assert loaded_data["dockerfiles"] == test_dockerfiles
        assert "summary" in loaded_data
        assert loaded_data["summary"]["dockerfile_count"] == 1

        # Save path for checking after context exits
        saved_path = temp_path

    # Assert - file is cleaned up after context exits
    assert not saved_path.exists()


@patch("cartography.intel.github.dockerfiles.get_dockerfiles_for_repos")
@patch("cartography.intel.github.dockerfiles.get_ecr_images_with_history")
@patch("cartography.intel.github.dockerfiles.match_images_to_dockerfiles")
def test_sync_with_dockerfiles(
    mock_match, mock_get_ecr_images_with_history, mock_get_dockerfiles, neo4j_session
):
    """
    Test the full sync function when Dockerfiles are found.
    """
    # Arrange
    mock_dockerfiles = [
        {
            "repo_url": "https://github.com/testorg/testrepo",
            "repo_name": "testorg/testrepo",
            "path": "Dockerfile",
            "content": DOCKERFILE_CONTENT,
        }
    ]
    mock_get_dockerfiles.return_value = mock_dockerfiles
    mock_get_ecr_images_with_history.return_value = []  # No ECR images
    mock_match.return_value = []  # No matches

    # Act
    result = cartography.intel.github.dockerfiles.sync(
        neo4j_session=neo4j_session,
        token="test_token",
        api_url=TEST_GITHUB_URL,
        organization="testorg",
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=TEST_JOB_PARAMS,
        repos=TEST_REPOS,
    )

    # Assert
    mock_get_dockerfiles.assert_called_once_with(
        "test_token",
        TEST_REPOS,
        "https://api.github.com",
        org="testorg",
    )
    mock_get_ecr_images_with_history.assert_called_once()
    assert result is not None
    assert result.dockerfile_count == 1
    assert result.dockerfiles == mock_dockerfiles


@patch("cartography.intel.github.dockerfiles.get_dockerfiles_for_repos")
def test_sync_no_dockerfiles(mock_get_dockerfiles, neo4j_session):
    """
    Test that sync returns None when no Dockerfiles are found.
    """
    # Arrange
    mock_get_dockerfiles.return_value = []

    # Act
    result = cartography.intel.github.dockerfiles.sync(
        neo4j_session=neo4j_session,
        token="test_token",
        api_url=TEST_GITHUB_URL,
        organization="testorg",
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=TEST_JOB_PARAMS,
        repos=TEST_REPOS,
    )

    # Assert
    assert result is None


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_search_handles_http_error_gracefully(mock_rest_api):
    """
    Test that search_dockerfiles_in_repo handles HTTP errors gracefully.
    """
    import requests

    # Arrange - simulate a 403 rate limit error
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_rest_api.side_effect = requests.exceptions.HTTPError(response=mock_response)

    # Act
    results = cartography.intel.github.dockerfiles.search_dockerfiles_in_repo(
        token="test_token",
        owner="testorg",
        repo="testrepo",
        base_url="https://api.github.com",
    )

    # Assert - should return empty list, not raise exception
    assert results == []


@patch("cartography.intel.github.dockerfiles.call_github_rest_api")
def test_get_file_content_handles_not_found(mock_rest_api):
    """
    Test that get_file_content returns None when file is not found.
    """
    import requests

    # Arrange - simulate a 404 not found error
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_rest_api.side_effect = requests.exceptions.HTTPError(response=mock_response)

    # Act
    content = cartography.intel.github.dockerfiles.get_file_content(
        token="test_token",
        owner="testorg",
        repo="testrepo",
        path="nonexistent/Dockerfile",
        base_url="https://api.github.com",
    )

    # Assert
    assert content is None
