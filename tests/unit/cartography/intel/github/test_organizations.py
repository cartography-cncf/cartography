from unittest.mock import patch

import pytest
import requests

import cartography.intel.github.util
from cartography.intel.github.organizations import get


def _http_error(status):
    response = requests.Response()
    response.status_code = status
    return requests.exceptions.HTTPError(response=response)


@patch.object(
    cartography.intel.github.util,
    "call_github_rest_api",
    side_effect=_http_error(502),
)
def test_get_settings_unexpected_error_propagates(mock_rest):
    # Act and assert
    with pytest.raises(requests.exceptions.HTTPError):
        get("token", "https://api.github.com/graphql", "simpsoncorp")
