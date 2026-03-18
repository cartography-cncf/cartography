from unittest.mock import Mock
from unittest.mock import patch

import pytest
from requests import Response
from requests.exceptions import HTTPError

from cartography.intel.github import repos


def _build_http_error(status_code: int) -> HTTPError:
    response = Response()
    response.status_code = status_code
    return HTTPError(f"http-{status_code}", response=response)


@patch("cartography.intel.github.repos.get_org_repos")
@patch("cartography.intel.github.repos.fetch_all")
def test_get_falls_back_to_rest_on_transient_graphql_error(
    mock_fetch_all: Mock,
    mock_get_org_repos: Mock,
) -> None:
    mock_fetch_all.side_effect = _build_http_error(502)
    mock_get_org_repos.return_value = [
        {
            "name": "sample-repo",
            "full_name": "example-org/sample-repo",
            "language": "Python",
            "html_url": "https://github.com/example-org/sample-repo",
            "ssh_url": "git@github.com:example-org/sample-repo.git",
            "created_at": "2024-01-01T00:00:00Z",
            "description": "sample",
            "updated_at": "2024-01-02T00:00:00Z",
            "homepage": "https://example.com",
            "default_branch": "main",
            "private": False,
            "archived": False,
            "disabled": False,
            "locked": False,
            "owner": {
                "login": "example-org",
                "html_url": "https://github.com/example-org",
                "type": "Organization",
            },
        },
    ]

    result = repos.get("token", "https://api.github.com/graphql", "example-org")

    assert result == [
        {
            "name": "sample-repo",
            "nameWithOwner": "example-org/sample-repo",
            "primaryLanguage": {"name": "Python"},
            "url": "https://github.com/example-org/sample-repo",
            "sshUrl": "git@github.com:example-org/sample-repo.git",
            "createdAt": "2024-01-01T00:00:00Z",
            "description": "sample",
            "updatedAt": "2024-01-02T00:00:00Z",
            "homepageUrl": "https://example.com",
            "languages": {"totalCount": 0, "nodes": []},
            "defaultBranchRef": {"name": "main", "id": None},
            "isPrivate": False,
            "isArchived": False,
            "isDisabled": False,
            "isLocked": False,
            "owner": {
                "url": "https://github.com/example-org",
                "login": "example-org",
                "__typename": "Organization",
            },
            "collaborators": None,
            "requirements": None,
            "setupCfg": None,
        },
    ]
    mock_get_org_repos.assert_called_once_with("example-org", "token", "https://api.github.com/graphql")


@patch("cartography.intel.github.repos.get_org_repos")
@patch("cartography.intel.github.repos.fetch_all")
def test_get_reraises_non_transient_graphql_error(
    mock_fetch_all: Mock,
    mock_get_org_repos: Mock,
) -> None:
    mock_fetch_all.side_effect = _build_http_error(401)

    with pytest.raises(HTTPError):
        repos.get("token", "https://api.github.com/graphql", "example-org")

    mock_get_org_repos.assert_not_called()
