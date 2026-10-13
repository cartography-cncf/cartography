from datetime import datetime
from datetime import timezone
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.zoom.access import sync_roles
from cartography.intel.zoom.client import RequestBudget
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.client import ZoomRequestLimitError
from cartography.intel.zoom.util import date_windows
from cartography.intel.zoom.util import fetch_many
from cartography.intel.zoom.util import is_zoom_error
from cartography.intel.zoom.util import optional_call
from tests.data.zoom.security import USERS
from tests.unit.cartography.intel.zoom.test_client import response


def get_detail(client: ZoomClient, path: str) -> dict[str, Any]:
    return client.get(path)


def test_optional_permissions_are_not_successful_empty_or_bad_credentials() -> None:
    # Arrange
    def failure(status: int, code: int, message: str | None = "") -> None:
        raise requests.HTTPError(
            response=response(status, {"code": code, "message": message})
        )

    # Act and assert
    for status, code in ((403, 0), (400, 200)):
        assert optional_call("roles", lambda: failure(status, code)) is None
    for status, code, message in (
        (401, 124, ""),
        (400, 124, ""),
        (500, 0, ""),
        (400, 4700, ""),
        (400, 4700, "Token cannot be empty."),
        (400, 4700, "Exception message"),
        (400, 4700, None),
        (400, 4711, "Refresh token invalid."),
        (400, 4711, ""),
        (400, 4711, None),
    ):
        with pytest.raises(requests.HTTPError):
            optional_call("roles", lambda: failure(status, code, message))
    assert optional_call("roles", lambda: []) == []


@pytest.mark.parametrize(  # type: ignore[misc]
    "code,message",
    [
        (4700, "Invalid access token, does not contain role:read:admin scope."),
        (
            4711,
            "Invalid access token, does not contain scopes:[group:read:settings:admin].",
        ),
    ],
)
def test_missing_scope_is_cached_for_only_the_affected_surface(
    code: int, message: str
) -> None:
    # Arrange
    unavailable: set[str] = set()
    denied = MagicMock(
        side_effect=requests.HTTPError(
            response=response(400, {"code": code, "message": message})
        )
    )
    healthy = MagicMock(return_value={"waiting_room": True})

    # Act
    first = optional_call("group configured settings", denied, unavailable)
    second = optional_call("group configured settings", denied, unavailable)
    other = optional_call("group locked settings", healthy, unavailable)

    # Assert
    assert first is None and second is None
    denied.assert_called_once_with()
    healthy.assert_called_once_with()
    assert other == {"waiting_room": True}
    assert unavailable == {"group configured settings"}


@pytest.mark.parametrize("status,code", [(403, 0), (400, 200)])  # type: ignore[misc]
def test_owner_denials_do_not_disable_later_owners(status: int, code: int) -> None:
    # Arrange
    unavailable: set[str] = set()
    fetch = MagicMock(
        side_effect=[
            requests.HTTPError(response=response(status, {"code": code})),
            {"waiting_room": True},
        ]
    )

    # Act
    first = optional_call("user configured settings", fetch, unavailable)
    second = optional_call("user configured settings", fetch, unavailable)

    # Assert
    assert first is None
    assert second == {"waiting_room": True}
    assert fetch.call_count == 2
    assert unavailable == set()


def test_paginated_reads_fail_before_returning_incomplete_data() -> None:
    # Arrange
    client = ZoomClient("account-a", "client", "secret")
    # Act and assert
    with (
        client.session,
        patch.object(
            client,
            "get",
            side_effect=[
                {"apps": [{"app_id": "a"}], "next_page_token": "page2"},
                {"apps": [], "next_page_token": "page2"},
            ],
        ),
    ):
        with pytest.raises(ValueError, match="repeated"):
            client.get_paginated("/marketplace/apps", "apps")
    with patch.object(client, "get", return_value={"apps": [], "total_records": 1}):
        with pytest.raises(ValueError, match="all records"):
            client.get_paginated("/marketplace/apps", "apps")


def test_budget_and_origin_validation_apply_before_network() -> None:
    # Arrange
    client = ZoomClient("a", "b", "c", RequestBudget(remaining=0))
    # Act and assert
    with client.session:
        for path in (
            "https://example.com/users",
            "//example.com/users",
            "/users?secret=x",
        ):
            with pytest.raises(ValueError, match="relative"):
                client.get(path)
        with pytest.raises(ZoomRequestLimitError, match="request limit"):
            client.get("/roles")
        fork = client.fork()
        with fork.session, pytest.raises(ZoomRequestLimitError):
            fork.get("/roles")


@pytest.mark.parametrize(  # type: ignore[misc]
    "error",
    [
        ZoomRequestLimitError("Zoom sync reached its configured request limit"),
        requests.HTTPError(response=response(429, {"code": 429})),
    ],
)
def test_limits_and_sustained_rate_limits_skip_the_rest_of_one_surface(
    error: Exception,
) -> None:
    # Arrange
    unavailable: set[str] = set()
    limited = MagicMock(side_effect=error)
    healthy = MagicMock(return_value={"id": 1})

    # Act
    first = optional_call("meetings", limited, unavailable)
    second = optional_call("meetings", limited, unavailable)
    other = optional_call("recordings", healthy, unavailable)

    # Assert
    assert first is None and second is None
    limited.assert_called_once_with()
    assert other == {"id": 1}
    assert unavailable == {"meetings"}


def test_endpoint_errors_match_only_the_documented_status_and_code() -> None:
    # Arrange
    def error(status: int, body: Any) -> requests.HTTPError:
        return requests.HTTPError(response=response(status, body))

    # Act and assert
    assert is_zoom_error(error(404, {"code": 3001}), 404, 3001)
    assert not is_zoom_error(error(404, {"code": 1001}), 404, 3001)
    assert not is_zoom_error(error(400, {"code": 3001}), 404, 3001)
    assert not is_zoom_error(requests.HTTPError(), 404, 3001)


def test_fetch_many_preserves_order_and_closes_worker_sessions() -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    workers = []

    def fork() -> MagicMock:
        worker = MagicMock(spec=ZoomClient)
        worker.session = MagicMock()
        worker.get.side_effect = lambda path: {"path": path}
        workers.append(worker)
        return worker

    client.fork.side_effect = fork
    paths = [f"/roles/{i}" for i in range(9)]
    # Act
    result = fetch_many(client, paths, get_detail)
    # Assert
    assert result == [{"path": path} for path in paths]
    assert len(workers) <= 4
    assert all(worker.session.__exit__.call_count == 1 for worker in workers)


def test_date_windows_split_month_boundaries() -> None:
    # Arrange
    with patch("cartography.intel.zoom.util.datetime") as clock:
        clock.now.return_value = datetime(2026, 10, 2, tzinfo=timezone.utc)
        # Act
        windows = date_windows(7)
    # Assert
    assert windows == [
        {"from": "2026-09-26", "to": "2026-09-30"},
        {"from": "2026-10-01", "to": "2026-10-02"},
    ]


def test_roles_reject_incomplete_inventory_before_graph_writes() -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.get.return_value = {"roles": [], "total_records": 1}
    session = MagicMock()

    # Act and assert
    with pytest.raises(ValueError, match="roles response"):
        sync_roles(session, client, "account-a", 2, USERS)
    client.get.assert_called_once_with("/roles")
    client.fork.assert_not_called()
    assert not session.mock_calls


def test_fetch_single_detail_reuses_the_existing_session() -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.get.return_value = {"id": "role-1"}

    # Act
    result = fetch_many(client, ["/roles/role-1"], get_detail)

    # Assert
    assert result == [{"id": "role-1"}]
    client.get.assert_called_once_with("/roles/role-1")
    client.fork.assert_not_called()
