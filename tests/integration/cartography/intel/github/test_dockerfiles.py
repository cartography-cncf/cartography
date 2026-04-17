from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.github.supply_chain
from tests.data.github.dockerfiles import DOCKERFILE_CONTENT
from tests.data.github.dockerfiles import DOCKERFILE_DEV_CONTENT
from tests.data.github.dockerfiles import DOCKERFILE_PROD_CONTENT
from tests.data.github.dockerfiles import FILE_CONTENT_DOCKERFILE
from tests.data.github.dockerfiles import FILE_CONTENT_DOCKERFILE_DEV
from tests.data.github.dockerfiles import FILE_CONTENT_DOCKERFILE_PROD
from tests.data.github.dockerfiles import SEARCH_DOCKERFILES_EMPTY_RESPONSE
from tests.data.github.dockerfiles import SEARCH_DOCKERFILES_ORG_RESPONSE
from tests.data.github.dockerfiles import TEST_REPOS

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://api.github.com/graphql"


@patch("cartography.intel.github.supply_chain.call_github_rest_api")
def test_search_dockerfiles_in_org(mock_rest_api):
    """
    Test that search_dockerfiles_in_org correctly calls the GitHub Code Search API
    with org-wide query and returns the expected results.
    """
    # Arrange
    mock_rest_api.return_value = SEARCH_DOCKERFILES_ORG_RESPONSE

    # Act
    results = cartography.intel.github.supply_chain.search_dockerfiles_in_org(
        token="test_token",
        org="testorg",
        base_url="https://api.github.com",
    )

    # Assert
    assert len(results) == 3
    assert results[0]["path"] == "Dockerfile"
    assert results[0]["repository"]["full_name"] == "testorg/testrepo"


@patch("cartography.intel.github.supply_chain.call_github_rest_api")
def test_search_dockerfiles_in_org_with_pagination(mock_rest_api):
    """
    Test that search_dockerfiles_in_org handles pagination correctly.
    """
    # Arrange - simulate 2 pages of results
    # Page 1 must have exactly 100 items to trigger pagination
    page1_items = [SEARCH_DOCKERFILES_ORG_RESPONSE["items"][0]] * 100
    page1_response = {
        "total_count": 150,
        "incomplete_results": False,
        "items": page1_items,
    }
    # Page 2 has fewer than 100 items, so pagination stops
    page2_response = {
        "total_count": 150,
        "incomplete_results": False,
        "items": [SEARCH_DOCKERFILES_ORG_RESPONSE["items"][0]] * 50,
    }
    mock_rest_api.side_effect = [page1_response, page2_response]

    # Act
    results = cartography.intel.github.supply_chain.search_dockerfiles_in_org(
        token="test_token",
        org="testorg",
        base_url="https://api.github.com",
    )

    # Assert - pagination should have collected all items from both pages
    assert len(results) == 150  # 100 + 50 items


@patch("cartography.intel.github.supply_chain.call_github_rest_api")
def test_search_dockerfiles_in_org_propagates_http_error(mock_rest_api):
    """
    Test that search_dockerfiles_in_org propagates HTTP errors (fail-fast).

    403 errors (rate limit, forbidden) should propagate to the caller so
    the sync can fail loudly rather than silently returning empty results.
    """
    import pytest
    import requests

    # Arrange - simulate a 403 rate limit error
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.reason = "Forbidden"
    mock_rest_api.side_effect = requests.exceptions.HTTPError(response=mock_response)

    # Act & Assert - should raise exception, not swallow it
    with pytest.raises(requests.exceptions.HTTPError):
        cartography.intel.github.supply_chain.search_dockerfiles_in_org(
            token="test_token",
            org="testorg",
            base_url="https://api.github.com",
        )


@patch("cartography.intel.github.supply_chain.call_github_rest_api")
def test_get_file_content(mock_rest_api):
    """
    Test that get_file_content correctly downloads and decodes file content.
    """
    # Arrange
    mock_rest_api.return_value = FILE_CONTENT_DOCKERFILE

    # Act
    content = cartography.intel.github.supply_chain.get_file_content(
        token="test_token",
        owner="testorg",
        repo="testrepo",
        path="Dockerfile",
        base_url="https://api.github.com",
    )

    # Assert
    assert content == DOCKERFILE_CONTENT


@patch("cartography.intel.github.supply_chain.call_github_rest_api")
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
    results = cartography.intel.github.supply_chain.get_dockerfiles_for_repos(
        token="test_token",
        repos=TEST_REPOS,
        org="testorg",
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


@patch("cartography.intel.github.supply_chain.get_dockerfiles_for_repos")
@patch(
    "cartography.intel.github.supply_chain.get_unmatched_container_images_with_history"
)
@patch("cartography.intel.github.supply_chain.match_images_to_dockerfiles")
def test_sync_with_dockerfiles(
    mock_match,
    mock_get_unmatched_images,
    mock_get_dockerfiles,
    neo4j_session,
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
    mock_get_unmatched_images.return_value = []  # No unmatched container images
    mock_match.return_value = []  # No matches

    # Act - sync now returns None
    cartography.intel.github.supply_chain.sync(
        neo4j_session=neo4j_session,
        token="test_token",
        api_url=TEST_GITHUB_URL,
        organization="testorg",
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=TEST_JOB_PARAMS,
        repos=TEST_REPOS,
    )

    # Assert - dockerfiles were fetched (unmatched images empty, so no matching called)
    mock_get_dockerfiles.assert_not_called()  # No unmatched images → no dockerfile search


@patch(
    "cartography.intel.github.supply_chain.get_unmatched_container_images_with_history"
)
def test_sync_no_unmatched_images(mock_get_unmatched_images, neo4j_session):
    """
    Test that sync skips dockerfile search when there are no unmatched images.
    """
    # Arrange
    mock_get_unmatched_images.return_value = []

    # Act - sync now returns None
    cartography.intel.github.supply_chain.sync(
        neo4j_session=neo4j_session,
        token="test_token",
        api_url=TEST_GITHUB_URL,
        organization="testorg",
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=TEST_JOB_PARAMS,
        repos=TEST_REPOS,
    )


@patch("cartography.intel.github.supply_chain.call_github_rest_api")
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
    content = cartography.intel.github.supply_chain.get_file_content(
        token="test_token",
        owner="testorg",
        repo="testrepo",
        path="nonexistent/Dockerfile",
        base_url="https://api.github.com",
    )

    # Assert
    assert content is None
