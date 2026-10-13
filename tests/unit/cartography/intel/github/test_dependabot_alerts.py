from unittest.mock import patch

import requests

import cartography.intel.github.dependabot_alerts
from cartography.intel.github.dependabot_alerts import DependabotAlertsFetchResult

TEST_GITHUB_URL = "https://api.github.com/graphql"
TEST_GITHUB_ENTERPRISE_URL = "https://fake.github.net/graphql/"
TEST_ORGANIZATION = "simpsoncorp"
FAKE_API_KEY = "asdf"


@patch.object(
    cartography.intel.github.dependabot_alerts,
    "fetch_all_rest_api_pages",
    return_value=[],
)
def test_get_dependabot_alerts_uses_public_github_api_version(mock_fetch):
    result = cartography.intel.github.dependabot_alerts.get(
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    assert result == DependabotAlertsFetchResult(alerts=[], cleanup_safe=True)
    mock_fetch.assert_called_once_with(
        FAKE_API_KEY,
        "https://api.github.com",
        "/orgs/simpsoncorp/dependabot/alerts",
        "",
        params={
            "state": "open,fixed,dismissed,auto_dismissed",
            "per_page": 100,
        },
        raise_on_status=(403, 404),
        api_version="2026-03-10",
    )


@patch.object(
    cartography.intel.github.dependabot_alerts,
    "fetch_all_rest_api_pages",
    return_value=[],
)
def test_get_dependabot_alerts_uses_enterprise_default_api_version(mock_fetch):
    result = cartography.intel.github.dependabot_alerts.get(
        FAKE_API_KEY,
        TEST_GITHUB_ENTERPRISE_URL,
        TEST_ORGANIZATION,
    )

    assert result == DependabotAlertsFetchResult(alerts=[], cleanup_safe=True)
    mock_fetch.assert_called_once_with(
        FAKE_API_KEY,
        "https://fake.github.net/v3",
        "/orgs/simpsoncorp/dependabot/alerts",
        "",
        params={
            "state": "open,fixed,dismissed,auto_dismissed",
            "per_page": 100,
        },
        raise_on_status=(403, 404),
    )


@patch.object(
    cartography.intel.github.dependabot_alerts,
    "fetch_all_rest_api_pages",
)
def test_get_dependabot_alerts_marks_403_fetch_as_not_cleanup_safe(mock_fetch):
    response = requests.Response()
    response.status_code = 403
    mock_fetch.side_effect = requests.exceptions.HTTPError(response=response)

    result = cartography.intel.github.dependabot_alerts.get(
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    assert result == DependabotAlertsFetchResult(alerts=[], cleanup_safe=False)
