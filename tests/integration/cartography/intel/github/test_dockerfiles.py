import json
import os
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
def test_get_dockerfiles_for_repos(mock_rest_api):
    """
    Test that get_dockerfiles_for_repos correctly searches and downloads
    Dockerfiles from multiple repositories.
    """

    # Arrange
    def mock_api_response(endpoint, token, base_url, params=None):
        if "/search/code" in endpoint:
            # Return dockerfiles only for first repo, empty for second
            if "testrepo" in params.get("q", ""):
                return SEARCH_DOCKERFILES_RESPONSE
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


def test_write_dockerfiles_to_tempfile():
    """
    Test that write_dockerfiles_to_tempfile creates a valid JSON file.
    """
    # Arrange
    test_data = [
        {
            "repo_url": "https://github.com/test/repo",
            "repo_name": "test/repo",
            "path": "Dockerfile",
            "content": "FROM python:3.11",
        }
    ]

    # Act
    temp_path = cartography.intel.github.dockerfiles.write_dockerfiles_to_tempfile(
        test_data
    )

    # Assert
    assert temp_path.exists()
    assert temp_path.suffix == ".json"
    assert "github_dockerfiles_" in temp_path.name

    with open(temp_path) as f:
        loaded_data = json.load(f)
    assert loaded_data == test_data

    # Cleanup
    os.unlink(temp_path)


@patch("cartography.intel.github.dockerfiles.get_dockerfiles_for_repos")
@patch("cartography.intel.github.dockerfiles.write_dockerfiles_to_tempfile")
def test_sync_with_dockerfiles(mock_write, mock_get_dockerfiles, neo4j_session):
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

    from pathlib import Path

    mock_temp_path = Path("/tmp/test_dockerfiles.json")
    mock_write.return_value = mock_temp_path

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
    mock_get_dockerfiles.assert_called_once()
    mock_write.assert_called_once_with(mock_dockerfiles)
    assert result == mock_temp_path


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
