import json
import typing
from base64 import b64encode
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from datetime import timezone as tz
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from requests import Response
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError

import cartography.intel.github.packages
from cartography.intel.github.util import _GRAPHQL_RATE_LIMIT_REMAINING_THRESHOLD
from cartography.intel.github.util import fetch_all
from cartography.intel.github.util import fetch_all_rest_api_pages
from cartography.intel.github.util import handle_rate_limit_sleep
from tests.data.github.rate_limit import RATE_LIMIT_RESPONSE_JSON


@patch("cartography.intel.github.repos.cleanup_orphaned_github_branches")
@patch("cartography.intel.github.repos.cleanup_global_resources")
@patch("cartography.intel.github.users.cleanup")
@patch("cartography.intel.github.supply_chain.sync")
@patch(
    "cartography.intel.github.container_image_attestations.sync_container_image_attestations"
)
@patch("cartography.intel.github.container_image_tags.sync_container_image_tags")
@patch(
    "cartography.intel.github.container_images.sync_container_images",
    return_value=([], [], [], set()),
)
@patch(
    "cartography.intel.github.packages.sync_packages",
    return_value=cartography.intel.github.packages.ContainerPackagesFetchResult(
        packages=[],
        cleanup_safe=True,
    ),
)
@patch("cartography.intel.github.repos.get", return_value=[])
@patch("cartography.intel.github.commits.sync_github_commits")
@patch("cartography.intel.github._get_repos_from_graph", return_value=[])
@patch("cartography.intel.github.actions.sync", return_value=[])
@patch("cartography.intel.github.teams.sync_github_teams")
@patch("cartography.intel.github.repos.sync")
@patch("cartography.intel.github.users.sync")
@patch("cartography.intel.github.make_credential", side_effect=["token-1", "token-2"])
def test_start_github_ingestion_defers_global_cleanup_until_after_all_orgs(
    mock_make_credential: Mock,
    mock_users_sync: Mock,
    mock_repos_sync: Mock,
    mock_teams_sync: Mock,
    mock_actions_sync: Mock,
    mock_get_repos_from_graph: Mock,
    mock_sync_github_commits: Mock,
    mock_get_repos: Mock,
    mock_packages_sync: Mock,
    mock_container_images_sync: Mock,
    mock_container_tags_sync: Mock,
    mock_attestations_sync: Mock,
    mock_supply_chain_sync: Mock,
    mock_users_cleanup: Mock,
    mock_cleanup_global_resources: Mock,
    mock_cleanup_orphaned_branches: Mock,
) -> None:
    github_config = {
        "organization": [
            {"name": "org-1", "url": "https://api.github.com/graphql"},
            {"name": "org-2", "url": "https://api.github.com/graphql"},
        ],
    }
    config = Mock(
        github_config=b64encode(json.dumps(github_config).encode()).decode(),
        update_tag=123,
        github_commit_lookback_days=7,
    )

    from cartography.intel.github import start_github_ingestion

    neo4j_session = Mock()
    start_github_ingestion(neo4j_session, config)

    assert mock_users_sync.call_count == 2
    assert mock_repos_sync.call_count == 2
    mock_users_cleanup.assert_called_once_with(neo4j_session, {"UPDATE_TAG": 123})
    mock_cleanup_global_resources.assert_called_once_with(
        neo4j_session,
        {"UPDATE_TAG": 123},
    )
    mock_cleanup_orphaned_branches.assert_called_once_with(
        neo4j_session,
        {"UPDATE_TAG": 123},
    )
    assert mock_supply_chain_sync.call_count == 0


@patch("cartography.intel.github.cleanup_unscoped_github_resources")
@patch("cartography.intel.github.supply_chain.sync")
@patch(
    "cartography.intel.github.container_image_attestations.sync_container_image_attestations"
)
@patch("cartography.intel.github.container_image_tags.sync_container_image_tags")
@patch(
    "cartography.intel.github.container_images.sync_container_images",
    return_value=([], [], [], set()),
)
@patch(
    "cartography.intel.github.packages.sync_packages",
    return_value=cartography.intel.github.packages.ContainerPackagesFetchResult(
        packages=[],
        cleanup_safe=True,
    ),
)
@patch("cartography.intel.github.repos.get", return_value=[])
@patch("cartography.intel.github.commits.sync_github_commits")
@patch("cartography.intel.github._get_repos_from_graph", return_value=[])
@patch("cartography.intel.github.actions.sync", return_value=[])
@patch("cartography.intel.github.teams.sync_github_teams")
@patch("cartography.intel.github.repos.sync")
@patch("cartography.intel.github.users.sync")
@patch("cartography.intel.github.make_credential", return_value="token-1")
def test_start_github_ingestion_can_skip_unscoped_cleanup(
    mock_make_credential: Mock,
    mock_users_sync: Mock,
    mock_repos_sync: Mock,
    mock_teams_sync: Mock,
    mock_actions_sync: Mock,
    mock_get_repos_from_graph: Mock,
    mock_sync_github_commits: Mock,
    mock_get_repos: Mock,
    mock_packages_sync: Mock,
    mock_container_images_sync: Mock,
    mock_container_tags_sync: Mock,
    mock_attestations_sync: Mock,
    mock_supply_chain_sync: Mock,
    mock_cleanup_unscoped_github_resources: Mock,
) -> None:
    github_config = {
        "organization": [
            {"name": "org-1", "url": "https://api.github.com/graphql"},
        ],
    }
    config = Mock(
        github_config=b64encode(json.dumps(github_config).encode()).decode(),
        update_tag=123,
        github_commit_lookback_days=7,
    )

    from cartography.intel.github import start_github_ingestion

    neo4j_session = Mock()
    start_github_ingestion(neo4j_session, config, skip_unscoped_cleanup=True)

    mock_make_credential.assert_called_once_with(github_config["organization"][0])
    mock_users_sync.assert_called_once()
    mock_repos_sync.assert_called_once()
    mock_cleanup_unscoped_github_resources.assert_not_called()
    assert mock_supply_chain_sync.call_count == 0


@patch("cartography.intel.github.repos.cleanup_orphaned_github_branches")
@patch("cartography.intel.github.repos.cleanup_global_resources")
@patch("cartography.intel.github.users.cleanup")
@patch("cartography.intel.github.make_credential")
def test_start_github_ingestion_skips_global_cleanup_when_no_orgs_configured(
    mock_make_credential: Mock,
    mock_users_cleanup: Mock,
    mock_cleanup_global_resources: Mock,
    mock_cleanup_orphaned_branches: Mock,
) -> None:
    github_config: dict[str, list[dict[str, str]]] = {"organization": []}
    config = Mock(
        github_config=b64encode(json.dumps(github_config).encode()).decode(),
        update_tag=123,
        github_commit_lookback_days=7,
    )

    from cartography.intel.github import start_github_ingestion

    neo4j_session = Mock()
    start_github_ingestion(neo4j_session, config)

    mock_make_credential.assert_not_called()
    mock_users_cleanup.assert_not_called()
    mock_cleanup_global_resources.assert_not_called()
    mock_cleanup_orphaned_branches.assert_not_called()


@patch("cartography.intel.github.repos.cleanup_orphaned_github_branches")
@patch("cartography.intel.github.repos.cleanup_global_resources")
@patch("cartography.intel.github.users.cleanup")
def test_cleanup_unscoped_github_resources(
    mock_users_cleanup: Mock,
    mock_cleanup_global_resources: Mock,
    mock_cleanup_orphaned_branches: Mock,
) -> None:
    from cartography.intel.github import cleanup_unscoped_github_resources

    neo4j_session = Mock()
    common_job_parameters = {"UPDATE_TAG": 123}

    cleanup_unscoped_github_resources(neo4j_session, common_job_parameters)

    mock_users_cleanup.assert_called_once_with(neo4j_session, common_job_parameters)
    mock_cleanup_global_resources.assert_called_once_with(
        neo4j_session,
        common_job_parameters,
    )
    mock_cleanup_orphaned_branches.assert_called_once_with(
        neo4j_session,
        common_job_parameters,
    )


@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.handle_rate_limit_sleep")
@patch("cartography.intel.github.util.fetch_page")
def test_fetch_all_handles_retries(
    mock_fetch_page: Mock,
    mock_handle_rate_limit_sleep: Mock,
    mock_sleep: Mock,
) -> None:
    """
    Ensures that fetch_all re-reaises the same exceptions when exceeding retry limit
    """
    # Arrange
    exception = HTTPError
    response = Response()
    response.status_code = 500
    mock_fetch_page.side_effect = exception("my-error", response=response)
    retries = 3
    # Act
    with pytest.raises(exception) as excinfo:
        fetch_all(
            "my-token",
            "my-api_url",
            "my-org",
            "my-query",
            "my-resource",
            retries=retries,
        )
    # Assert
    assert mock_handle_rate_limit_sleep.call_count == retries
    assert mock_fetch_page.call_count == retries
    assert "my-error" in str(excinfo.value)


@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.handle_rate_limit_sleep")
@patch("cartography.intel.github.util.fetch_page")
def test_fetch_all_reduces_count_on_502(
    mock_fetch_page: Mock,
    mock_handle_rate_limit_sleep: Mock,
    mock_sleep: Mock,
) -> None:
    response_502 = Response()
    response_502.status_code = 502
    success_response = {
        "data": {
            "organization": {
                "repositories": {
                    "nodes": [],
                    "edges": [],
                    "pageInfo": {"endCursor": None, "hasNextPage": False},
                },
                "url": "url",
                "login": "org",
            },
        }
    }
    mock_fetch_page.side_effect = [
        HTTPError("bad gateway", response=response_502),
        success_response,
    ]
    fetch_all("token", "api_url", "org", "query", "repositories", count=50)
    assert mock_fetch_page.call_count == 2
    assert mock_fetch_page.call_args_list[0][1]["count"] == 50
    assert mock_fetch_page.call_args_list[1][1]["count"] == 25


@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.handle_rate_limit_sleep")
@patch("cartography.intel.github.util.fetch_page")
def test_fetch_all_retries_connection_errors(
    mock_fetch_page: Mock,
    mock_handle_rate_limit_sleep: Mock,
    mock_sleep: Mock,
) -> None:
    response = {
        "data": {
            "organization": {
                "repositories": {
                    "nodes": [],
                    "edges": [],
                    "pageInfo": {"endCursor": None, "hasNextPage": False},
                },
                "url": "url",
                "login": "org",
            },
        }
    }
    mock_fetch_page.side_effect = [
        RequestsConnectionError("connection reset by peer"),
        response,
    ]

    fetch_all("token", "api_url", "org", "query", "repositories", retries=3)

    assert mock_fetch_page.call_count == 2
    mock_sleep.assert_called_once_with(2)


@typing.no_type_check
@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.handle_rate_limit_sleep")
@patch("cartography.intel.github.util.fetch_page")
def test_fetch_all_honors_retry_after_for_403(
    mock_fetch_page: Mock,
    mock_handle_rate_limit_sleep: Mock,
    mock_sleep: Mock,
) -> None:
    response_403 = Response()
    response_403.status_code = 403
    response_403.headers["retry-after"] = "65"
    response_403._content = b'{"message":"You have exceeded a secondary rate limit."}'
    success_response = {
        "data": {
            "organization": {
                "repositories": {
                    "nodes": [],
                    "edges": [],
                    "pageInfo": {"endCursor": None, "hasNextPage": False},
                },
                "url": "url",
                "login": "org",
            },
        }
    }
    mock_fetch_page.side_effect = [
        HTTPError("forbidden", response=response_403),
        success_response,
    ]

    fetch_all("token", "api_url", "org", "query", "repositories", retries=3)

    assert mock_fetch_page.call_count == 2
    mock_sleep.assert_called_once_with(65)


@typing.no_type_check
@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.handle_rate_limit_sleep")
@patch("cartography.intel.github.util.fetch_page")
@patch("cartography.intel.github.util.datetime")
def test_fetch_all_waits_for_rate_limit_reset_on_403(
    mock_datetime: Mock,
    mock_fetch_page: Mock,
    mock_handle_rate_limit_sleep: Mock,
    mock_sleep: Mock,
) -> None:
    mock_datetime.fromtimestamp = datetime.fromtimestamp
    now = datetime(
        year=2040,
        month=1,
        day=1,
        hour=19,
        minute=0,
        second=0,
        tzinfo=tz.utc,
    )
    mock_datetime.now = Mock(return_value=now)
    response_403 = Response()
    response_403.status_code = 403
    response_403.headers["x-ratelimit-remaining"] = "0"
    response_403.headers["x-ratelimit-reset"] = str(
        int((now + timedelta(minutes=2)).timestamp()),
    )
    response_403._content = b'{"message":"API rate limit exceeded"}'
    success_response = {
        "data": {
            "organization": {
                "repositories": {
                    "nodes": [],
                    "edges": [],
                    "pageInfo": {"endCursor": None, "hasNextPage": False},
                },
                "url": "url",
                "login": "org",
            },
        }
    }
    mock_fetch_page.side_effect = [
        HTTPError("forbidden", response=response_403),
        success_response,
    ]

    fetch_all("token", "api_url", "org", "query", "repositories", retries=3)

    mock_sleep.assert_called_once_with(timedelta(minutes=3).seconds)


@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.handle_rest_rate_limit_sleep")
@patch("cartography.intel.github.util.requests.get")
def test_fetch_all_rest_api_pages_retries_connection_errors(
    mock_requests_get: Mock,
    mock_handle_rest_rate_limit_sleep: Mock,
    mock_sleep: Mock,
) -> None:
    success_response = Mock(
        json=Mock(return_value={"items": [{"id": 1}]}),
        headers={},
    )
    success_response.raise_for_status = Mock()
    mock_requests_get.side_effect = [
        RequestsConnectionError("connection aborted"),
        success_response,
    ]

    result = fetch_all_rest_api_pages(
        "token", "https://api.github.com", "/endpoint", "items"
    )

    assert result == [{"id": 1}]
    assert mock_requests_get.call_count == 2
    assert mock_handle_rest_rate_limit_sleep.call_count == 2
    mock_sleep.assert_called_once_with(2)


@typing.no_type_check
@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.datetime")
@patch("cartography.intel.github.util.requests.get")
def test_handle_rate_limit_sleep(
    mock_requests_get: Mock,
    mock_datetime: Mock,
    mock_sleep: Mock,
) -> None:
    """
    Ensure we sleep to avoid the rate limit
    """
    # Arrange
    mock_datetime.fromtimestamp = datetime.fromtimestamp
    now = datetime(
        year=2040,
        month=1,
        day=1,
        hour=19,
        minute=0,
        second=0,
        tzinfo=tz.utc,
    )
    mock_datetime.now = Mock(return_value=now)
    reset = (now + timedelta(minutes=47)).timestamp()
    # sleep for one extra minute for safety
    expected_sleep_seconds = timedelta(minutes=48).seconds

    # above threshold
    resp_0 = deepcopy(RATE_LIMIT_RESPONSE_JSON)
    resp_0["resources"]["graphql"]["remaining"] = (
        _GRAPHQL_RATE_LIMIT_REMAINING_THRESHOLD + 1
    )
    resp_0["resources"]["graphql"]["reset"] = reset

    # below threshold
    resp_1 = deepcopy(RATE_LIMIT_RESPONSE_JSON)
    resp_1["resources"]["graphql"]["remaining"] = (
        _GRAPHQL_RATE_LIMIT_REMAINING_THRESHOLD - 1
    )
    resp_1["resources"]["graphql"]["reset"] = reset

    mock_requests_get.side_effect = [
        Mock(json=Mock(return_value=resp_0)),
        Mock(json=Mock(return_value=resp_1)),
    ]

    # Act
    handle_rate_limit_sleep("my-token")
    # Assert
    mock_datetime.now.assert_not_called()
    mock_sleep.assert_not_called()

    # reset mocks
    mock_datetime.reset_mock()
    mock_sleep.reset_mock()

    # Act
    handle_rate_limit_sleep("my-token")
    # Assert
    mock_datetime.now.assert_called_once_with(tz.utc)
    mock_sleep.assert_called_once_with(expected_sleep_seconds)
