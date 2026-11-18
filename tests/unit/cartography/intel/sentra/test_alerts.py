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


def test_get_violated_objects_loads_nothing_when_a_later_page_fails(mocker, caplog):
    # Arrange
    def get_page(_session, _api_url, _alert_id, offset, limit):
        if offset == 0:
            # A full first page, so the iterator asks for a second one.
            return {
                "items": [
                    {"id": f"object-{i}", "store_id": "store-a", "data_classes": []}
                    for i in range(limit)
                ],
            }
        raise _http_error(404)

    mocker.patch.object(api, "get_violated_objects_page", side_effect=get_page)

    # Act
    with caplog.at_level(logging.WARNING):
        result = list(
            alerts.get_violated_objects(
                None,
                "https://app.sentra.io",
                "alert-1",
            ),
        )

    # Assert
    assert result == []
    assert "HTTP 404" in caplog.text


def test_get_violated_objects_collapses_objects_with_the_same_store_and_classes(
    mocker,
):
    # Arrange
    mocker.patch.object(
        api,
        "get_violated_objects_page",
        return_value={
            "items": [
                {
                    "id": "object-1",
                    "store_id": "store-a",
                    "data_classes": [{"id": "c1"}],
                },
                {
                    "id": "object-2",
                    "store_id": "store-a",
                    "data_classes": [{"id": "c1"}],
                },
                {"id": "object-3", "store_id": "store-b", "data_classes": None},
            ],
        },
    )

    # Act
    result = list(
        alerts.get_violated_objects(None, "https://app.sentra.io", "alert-1"),
    )

    # Assert
    assert sorted(result, key=lambda o: o["store_id"]) == [
        {"store_id": "store-a", "data_classes": [{"id": "c1"}]},
        {"store_id": "store-b", "data_classes": []},
    ]
