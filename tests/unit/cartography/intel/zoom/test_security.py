from datetime import datetime
from datetime import timezone
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.zoom.access import sync_roles
from cartography.intel.zoom.activity import transform_events
from cartography.intel.zoom.client import RequestBudget
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import date_windows
from cartography.intel.zoom.util import fetch_many
from cartography.intel.zoom.util import optional_call
from tests.data.zoom.security import SIGNIN
from tests.data.zoom.security import USERS
from tests.unit.cartography.intel.zoom.test_client import response


def test_optional_permissions_are_not_successful_empty_or_bad_credentials() -> None:
    # Arrange
    def failure(status: int, code: int) -> None:
        raise requests.HTTPError(response=response(status, {"code": code}))

    # Act and assert
    for status, code in ((403, 0), (400, 200), (400, 4700), (400, 4711)):
        assert optional_call("roles", lambda: failure(status, code)) is None
    for status, code in ((401, 124), (400, 124), (500, 0), (429, 0)):
        with pytest.raises(requests.HTTPError):
            optional_call("roles", lambda: failure(status, code))
    assert optional_call("roles", lambda: []) == []


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
        with pytest.raises(ValueError, match="safety limit"):
            client.get("/roles")
        fork = client.fork()
        with fork.session, pytest.raises(ValueError, match="safety limit"):
            fork.get("/roles")


def test_fetch_many_preserves_order_and_closes_worker_sessions() -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    workers = []

    def fork() -> MagicMock:
        worker = MagicMock(spec=ZoomClient)
        worker.session = MagicMock()
        worker.get.side_effect = lambda path, params: {"path": path}
        workers.append(worker)
        return worker

    client.fork.side_effect = fork
    paths = [f"/roles/{i}" for i in range(9)]
    # Act
    result = fetch_many(client, paths)
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


def test_activity_retains_queryable_fields_without_free_text_or_ip() -> None:
    # Arrange
    event = {**SIGNIN, "operation_detail": "secret-placeholder", "meeting_number": None}
    # Act
    result = transform_events([event], "signins", "account-a", USERS)[0]
    # Assert
    assert result["user_node_id"] == USERS[0]["id"]
    assert result["occurred_at"] == datetime(2026, 9, 29, 12, tzinfo=timezone.utc)
    assert result["client_version"] == "6.1.0"
    assert result["meeting_node_id"] is None
    assert "secret-placeholder" not in str(result)
    assert "192.0.2.1" not in str(result)


@pytest.mark.parametrize(  # type: ignore[misc]
    "payload",
    [{"roles": None}, {"roles": {}}, {"roles": [], "total_records": 1}],
)
def test_roles_reject_incomplete_inventory_before_graph_writes(
    payload: dict[str, Any],
) -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.get.return_value = payload
    session = MagicMock()

    # Act and assert
    with pytest.raises(ValueError, match="roles response"):
        sync_roles(session, client, "account-a", 2, USERS)
    client.get.assert_called_once_with("/roles")
    client.fork.assert_not_called()
    assert not session.mock_calls
