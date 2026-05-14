"""Unit tests for GitHub runners sync helpers."""

from unittest.mock import Mock
from unittest.mock import patch

import requests

from cartography.intel.github.actions import _list_runners_tolerant
from cartography.intel.github.actions import transform_runners
from tests.data.github.runners import GET_ORG_RUNNERS


def _http_error(status_code: int) -> requests.exceptions.HTTPError:
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    return requests.exceptions.HTTPError(response=response)


def test_transform_runners_maps_intrinsic_fields() -> None:
    result = transform_runners(GET_ORG_RUNNERS)

    assert len(result) == 2
    assert result[0] == {
        "id": 23,
        "name": "linux-runner",
        "os": "linux",
        "status": "online",
        "busy": True,
        "ephemeral": False,
        "labels": ["self-hosted", "X64", "Linux"],
        "label_types": ["read-only", "read-only", "read-only"],
    }
    assert result[1]["labels"] == ["self-hosted", "X64", "macOS", "no-gpu"]
    assert result[1]["label_types"] == [
        "read-only",
        "read-only",
        "read-only",
        "custom",
    ]


def test_transform_runners_handles_missing_labels() -> None:
    result = transform_runners([{"id": 1, "name": "bare-runner"}])
    assert result == [
        {
            "id": 1,
            "name": "bare-runner",
            "os": None,
            "status": None,
            "busy": None,
            "ephemeral": None,
            "labels": [],
            "label_types": [],
        },
    ]


@patch("cartography.intel.github.actions.fetch_all_rest_api_pages")
def test_list_runners_tolerant_returns_none_on_403(mock_fetch_all) -> None:
    mock_fetch_all.side_effect = _http_error(403)
    assert (
        _list_runners_tolerant(
            "tok",
            "https://api.github.com",
            "/orgs/acme/actions/runners",
            "org runners",
        )
        is None
    )


@patch("cartography.intel.github.actions.fetch_all_rest_api_pages")
def test_list_runners_tolerant_propagates_non_403(mock_fetch_all) -> None:
    mock_fetch_all.side_effect = _http_error(500)
    try:
        _list_runners_tolerant(
            "tok",
            "https://api.github.com",
            "/orgs/acme/actions/runners",
            "org runners",
        )
        raise AssertionError("Expected HTTPError to propagate")
    except requests.exceptions.HTTPError:
        pass
