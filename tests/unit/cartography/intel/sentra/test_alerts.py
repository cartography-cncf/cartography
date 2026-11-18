import logging

import pytest
import requests

from cartography.intel.sentra import alerts
from cartography.intel.sentra import api


def _http_error(status_code: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    return requests.HTTPError(response=response)


@pytest.mark.parametrize("status_code", [404, 422])
def test_get_violated_objects_skips_alert_specific_errors(
    mocker,
    caplog,
    status_code,
):
    # Arrange
    mocker.patch.object(
        api,
        "get_violated_objects_page",
        side_effect=_http_error(status_code),
    )

    # Act
    with caplog.at_level(logging.WARNING):
        result = list(
            alerts.get_violated_objects(None, "https://app.sentra.io", "alert-1"),
        )

    # Assert
    assert result == []
    assert f"HTTP {status_code}" in caplog.text
    assert "alert-1" in caplog.text


@pytest.mark.parametrize("status_code", [401, 403, 500])
def test_get_violated_objects_raises_other_errors(mocker, status_code):
    # Arrange
    mocker.patch.object(
        api,
        "get_violated_objects_page",
        side_effect=_http_error(status_code),
    )

    # Act and assert
    with pytest.raises(requests.HTTPError):
        list(alerts.get_violated_objects(None, "https://app.sentra.io", "alert-1"))
