from unittest.mock import patch

import pytest
import requests

import cartography.intel.github.app_installations
import cartography.intel.github.util
import cartography.intel.github.webhooks


def _http_error(status):
    response = requests.Response()
    response.status_code = status
    return requests.exceptions.HTTPError(response=response)


@pytest.mark.parametrize(
    "module,call",
    [
        (
            cartography.intel.github.app_installations,
            lambda: cartography.intel.github.app_installations.get(
                "token", "https://api.github.com/graphql", "simpsoncorp"
            ),
        ),
        (
            cartography.intel.github.webhooks,
            lambda: cartography.intel.github.webhooks.get(
                "token", "https://api.github.com/graphql", "simpsoncorp", []
            ),
        ),
    ],
)
def test_unexpected_errors_propagate_instead_of_skipping(module, call):
    # Arrange
    with patch.object(
        cartography.intel.github.util,
        "fetch_all_rest_api_pages",
        side_effect=_http_error(502),
    ):
        # Act and assert
        with pytest.raises(requests.exceptions.HTTPError):
            call()
