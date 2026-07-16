from typing import Any
from unittest import mock

import pytest
import requests

from cartography.intel.vercel.util import paginated_get


def _make_response(
    payload: Any,
    status_code: int = 200,
) -> mock.MagicMock:
    resp = mock.MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def test_paginated_get_follows_next_cursor() -> None:
    # Arrange: two pages linked by a continuation cursor, then a null cursor.
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response(
            {
                "accessGroups": [{"accessGroupId": "ag_1"}],
                "pagination": {"count": 1, "next": "cursor_2"},
            },
        ),
        _make_response(
            {
                "accessGroups": [{"accessGroupId": "ag_2"}],
                "pagination": {"count": 1, "next": None},
            },
        ),
    ]

    # Act
    results = paginated_get(
        session,
        "https://api.vercel.com/v1/access-groups",
        "accessGroups",
        "team_1",
        pagination_param="next",
    )

    # Assert: both pages are returned and the loop terminates.
    assert results == [{"accessGroupId": "ag_1"}, {"accessGroupId": "ag_2"}]
    assert session.get.call_count == 2
    # The second request must carry the cursor under the `next` param (not `until`).
    second_call_params = session.get.call_args_list[1].kwargs["params"]
    assert second_call_params["next"] == "cursor_2"
    assert "until" not in second_call_params


def test_paginated_get_defaults_to_until_cursor() -> None:
    # Arrange: timestamp-cursor endpoints (e.g. deployments) page with `until`.
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response(
            {
                "deployments": [{"uid": "dpl_1"}],
                "pagination": {"count": 1, "next": 1700000000000},
            },
        ),
        _make_response(
            {
                "deployments": [{"uid": "dpl_2"}],
                "pagination": {"count": 1, "next": None},
            },
        ),
    ]

    # Act
    results = paginated_get(
        session,
        "https://api.vercel.com/v6/deployments",
        "deployments",
        "team_1",
    )

    # Assert: default preserves the historical `until` behavior.
    assert results == [{"uid": "dpl_1"}, {"uid": "dpl_2"}]
    second_call_params = session.get.call_args_list[1].kwargs["params"]
    assert second_call_params["until"] == 1700000000000
    assert "next" not in second_call_params


def test_paginated_get_stops_on_single_page() -> None:
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [
        _make_response(
            {
                "accessGroups": [{"accessGroupId": "ag_1"}],
                "pagination": {"count": 1, "next": None},
            },
        ),
    ]

    results = paginated_get(
        session,
        "https://api.vercel.com/v1/access-groups",
        "accessGroups",
        "team_1",
        pagination_param="next",
    )

    assert results == [{"accessGroupId": "ag_1"}]
    assert session.get.call_count == 1


def test_paginated_get_handles_bare_array_endpoint() -> None:
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [_make_response([{"id": "ec_1"}, {"id": "ec_2"}])]

    results = paginated_get(
        session,
        "https://api.vercel.com/v1/edge-config",
        "",
        "team_1",
    )

    assert results == [{"id": "ec_1"}, {"id": "ec_2"}]
    assert session.get.call_count == 1


def test_paginated_get_returns_partial_on_plan_gated_403() -> None:
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [_make_response(None, status_code=403)]

    results = paginated_get(
        session,
        "https://api.vercel.com/v1/access-groups",
        "accessGroups",
        "team_1",
        pagination_param="next",
    )

    assert results == []


def test_paginated_get_raises_on_missing_result_key() -> None:
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = [_make_response({"pagination": {"next": None}})]

    with pytest.raises(KeyError):
        paginated_get(
            session,
            "https://api.vercel.com/v1/access-groups",
            "accessGroups",
            "team_1",
            pagination_param="next",
        )
