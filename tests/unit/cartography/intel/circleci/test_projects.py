from unittest.mock import MagicMock

import pytest
import requests

from cartography.intel.circleci.projects import discover_project_slugs

BASE_URL = "https://circleci.fake/api/v2"
PIPELINE_FEED = {
    "items": [{"project_slug": "gh/acme/web"}],
    "next_page_token": None,
}


def _session(insights_status: int, insights_body: dict) -> MagicMock:
    def get(url, **kwargs):
        response = requests.Response()
        if url == f"{BASE_URL}/pipeline":
            response.status_code = 200
            response.json = lambda: PIPELINE_FEED
        elif url == f"{BASE_URL}/insights/gh/acme/summary":
            response.status_code = insights_status
            response.json = lambda: insights_body
        else:
            raise AssertionError(f"Unexpected URL: {url}")
        return response

    session = MagicMock()
    session.get.side_effect = get
    return session


@pytest.mark.parametrize(
    "insights_status,insights_body,expected",
    [
        pytest.param(
            200,
            {"all_projects": ["web", "api", "infra"]},
            {"gh/acme/web", "gh/acme/api", "gh/acme/infra"},
            id="projects the token owner does not follow are discovered",
        ),
        pytest.param(
            404,
            {"message": "Not found"},
            {"gh/acme/web"},
            id="falls back to the pipeline feed when the summary is unavailable",
        ),
    ],
)
def test_discover_project_slugs(insights_status, insights_body, expected):
    api_session = _session(insights_status, insights_body)

    assert discover_project_slugs(api_session, BASE_URL, "gh/acme") == expected
