import asyncio
from collections.abc import AsyncIterator
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kiota_abstractions.api_error import APIError

from cartography.intel.microsoft import credentials
from cartography.intel.microsoft.entra import app_role_assignments
from cartography.intel.microsoft.entra import applications
from cartography.intel.microsoft.entra import groups
from cartography.intel.microsoft.entra import ou
from cartography.intel.microsoft.entra import service_principals
from cartography.intel.microsoft.entra import users
from cartography.intel.microsoft.entra.ou import get_entra_ous
from cartography.intel.microsoft.entra.users import get_users


async def _collect(items: AsyncIterator[Any]) -> list[Any]:
    return [item async for item in items]


GRAPH_WAIT = "cartography.intel.microsoft.entra.utils.asyncio.sleep"


def _forbidden_error() -> APIError:
    error = APIError("forbidden")
    error.response_status_code = 403
    return error


OPTIONAL_REPORTS = pytest.mark.parametrize(
    ("getter", "report_path"),
    (
        (
            users.get_user_mfa_registrations,
            ("reports", "authentication_methods", "user_registration_details"),
        ),
        (users.get_risky_users, ("identity_protection", "risky_users")),
        (
            service_principals.get_risky_service_principals,
            ("identity_protection", "risky_service_principals"),
        ),
    ),
)


def _client_whose_report_fails(report_path: tuple[str, ...], status: int) -> Any:
    client = MagicMock()
    report = client
    for attribute in report_path:
        report = getattr(report, attribute)
    report.get = AsyncMock(
        side_effect=APIError("request failed", response_status_code=status)
    )
    return client


@OPTIONAL_REPORTS  # type: ignore[misc]
@pytest.mark.parametrize("status", [403, 429])  # type: ignore[misc]
@patch(GRAPH_WAIT, new=AsyncMock())
def test_optional_reports_are_unavailable_when_denied_or_throttled(
    getter, report_path: tuple[str, ...], status: int
) -> None:
    # Arrange
    client = _client_whose_report_fails(report_path, status)

    # Act
    report = asyncio.run(getter(client))

    # Assert
    assert report is None


@OPTIONAL_REPORTS  # type: ignore[misc]
@pytest.mark.parametrize("status", [401, 500])  # type: ignore[misc]
def test_optional_reports_propagate_other_errors(
    getter, report_path: tuple[str, ...], status: int
) -> None:
    # Arrange
    client = _client_whose_report_fails(report_path, status)

    # Act and assert
    with pytest.raises(APIError, match="request failed"):
        asyncio.run(getter(client))


@pytest.mark.parametrize(  # type: ignore[misc]
    ("retry_after_header", "expected_wait"),
    [({}, 30), ({"retry-after": "90"}, 90)],
    ids=["default_wait", "graph_asks_for_longer"],
)
def test_mfa_report_survives_throttling_on_a_later_page(
    retry_after_header: dict[str, str], expected_wait: int
) -> None:
    # Arrange
    client = MagicMock()
    report = client.reports.authentication_methods.user_registration_details
    report.get = AsyncMock(
        return_value=MagicMock(value=[MagicMock(id="user-1")], odata_next_link="next")
    )
    report.with_url.return_value.get = AsyncMock(
        side_effect=[
            APIError(
                "throttled",
                response_status_code=429,
                response_headers=retry_after_header,
            ),
            MagicMock(value=[MagicMock(id="user-2")], odata_next_link=None),
        ]
    )
    wait = AsyncMock()

    # Act
    with patch(GRAPH_WAIT, new=wait):
        registrations = asyncio.run(users.get_user_mfa_registrations(client))

    # Assert
    assert registrations is not None
    assert set(registrations) == {"user-1", "user-2"}
    report.get.assert_awaited_once()
    wait.assert_awaited_once_with(expected_wait)


def test_users_propagates_denial_from_later_page() -> None:
    # Arrange
    client = MagicMock()
    first_page = MagicMock(value=[MagicMock()], odata_next_link="next-page")
    client.users.get = AsyncMock(return_value=first_page)
    client.users.with_url.return_value.get = AsyncMock(side_effect=_forbidden_error())

    # Act and assert
    with pytest.raises(APIError, match="forbidden"):
        asyncio.run(_collect(get_users(client)))


def test_administrative_units_propagates_denial() -> None:
    # Arrange
    client = MagicMock()
    client.directory.administrative_units.get = AsyncMock(
        side_effect=_forbidden_error(),
    )

    # Act and assert
    with pytest.raises(APIError, match="forbidden"):
        asyncio.run(_collect(get_entra_ous(client)))


def test_delegated_users_loads_partial_batch_before_propagating_denial(
    monkeypatch,
    graph_client_class: MagicMock,
) -> None:
    # Arrange
    async def get_users_then_deny(client):
        yield [MagicMock(id="visible-user")], True
        raise _forbidden_error()

    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(users, "GraphServiceClient", graph_client_class)
    monkeypatch.setattr(users, "get_users", get_users_then_deny)
    load_users = MagicMock()
    monkeypatch.setattr(users, "load_users", load_users)

    # Act and assert
    with pytest.raises(APIError, match="forbidden"):
        asyncio.run(
            users.sync_entra_users(
                MagicMock(),
                "tenant-id",
                None,
                None,
                123,
                {"UPDATE_TAG": 123, "TENANT_ID": "tenant-id"},
                delegated_auth=True,
            )
        )

    load_users.assert_called_once()
    assert load_users.call_args.args[1][0]["id"] == "visible-user"


def test_delegated_groups_continues_after_denied_group_and_propagates_denial(
    monkeypatch,
) -> None:
    # Arrange
    denied_group = MagicMock(id="denied-group", display_name="Denied")
    visible_group = MagicMock(id="visible-group", display_name="Visible")

    async def get_groups(client):
        yield denied_group
        yield visible_group

    get_owners = AsyncMock(side_effect=[_forbidden_error(), []])
    member_pages: Iterator[list[tuple[list[str], list[str]]]] = iter(
        [[(["member-id"], [])], []]
    )

    async def get_member_pages(client, group_id):
        for page in next(member_pages):
            yield page

    get_members = MagicMock(side_effect=get_member_pages)
    graph_client = MagicMock()
    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(
        groups, "GraphServiceClient", MagicMock(return_value=graph_client)
    )
    monkeypatch.setattr(groups, "get_entra_groups", get_groups)
    monkeypatch.setattr(groups, "get_group_owners", get_owners)
    monkeypatch.setattr(groups, "get_group_member_pages", get_members)
    load_groups = MagicMock()
    monkeypatch.setattr(groups, "load_groups", load_groups)

    # Act and assert
    with pytest.raises(APIError, match="forbidden"):
        asyncio.run(
            groups.sync_entra_groups(
                MagicMock(),
                "tenant-id",
                None,
                None,
                123,
                {"UPDATE_TAG": 123, "TENANT_ID": "tenant-id"},
                delegated_auth=True,
            )
        )

    node_rows, member_rows = (call.args[1] for call in load_groups.call_args_list)
    assert {group["id"] for group in node_rows} == {
        "denied-group",
        "visible-group",
    }
    denied = next(group for group in node_rows if group["id"] == "denied-group")
    assert denied["owner_ids"] == []
    assert [(row["id"], row["member_ids"]) for row in member_rows] == [
        ("denied-group", ["member-id"])
    ]
    assert get_members.call_count == 2


def test_delegated_groups_preserves_owners_after_member_denial(monkeypatch) -> None:
    # Arrange
    group = MagicMock(id="group-id", display_name="Visible")

    async def get_groups(client):
        yield group

    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(groups, "GraphServiceClient", MagicMock())
    monkeypatch.setattr(groups, "get_entra_groups", get_groups)
    monkeypatch.setattr(
        groups, "get_group_owners", AsyncMock(return_value=["owner-id"])
    )

    async def denied_member_pages(client, group_id):
        raise _forbidden_error()
        yield

    monkeypatch.setattr(groups, "get_group_member_pages", denied_member_pages)
    load_groups = MagicMock()
    monkeypatch.setattr(groups, "load_groups", load_groups)

    # Act and assert
    with pytest.raises(APIError, match="forbidden"):
        asyncio.run(
            groups.sync_entra_groups(
                MagicMock(),
                "tenant-id",
                None,
                None,
                123,
                {"UPDATE_TAG": 123, "TENANT_ID": "tenant-id"},
                delegated_auth=True,
            )
        )

    loaded_group = load_groups.call_args.args[1][0]
    assert loaded_group["owner_ids"] == ["owner-id"]
    assert loaded_group["member_ids"] == []


@pytest.mark.parametrize(  # type: ignore[misc]
    ("module", "getter_name", "loader_name", "sync"),
    (
        (
            applications,
            "get_entra_applications",
            "load_applications",
            applications.sync_entra_applications,
        ),
        (
            service_principals,
            "get_entra_service_principals",
            "load_service_principals",
            service_principals.sync_service_principals,
        ),
        (ou, "get_entra_ous", "load_ous", ou.sync_entra_ous),
    ),
)
def test_delegated_collectors_load_partial_batch_before_propagating_denial(
    monkeypatch: pytest.MonkeyPatch,
    graph_client_class: MagicMock,
    module,
    getter_name: str,
    loader_name: str,
    sync,
) -> None:
    # Arrange
    async def get_one_then_deny(client):
        yield MagicMock(id="visible-record", login_url="")
        raise _forbidden_error()

    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(module, "GraphServiceClient", graph_client_class)
    monkeypatch.setattr(module, getter_name, get_one_then_deny)
    loader = MagicMock()
    monkeypatch.setattr(module, loader_name, loader)

    # Act and assert
    with pytest.raises(APIError, match="forbidden"):
        asyncio.run(
            sync(
                MagicMock(),
                "tenant-id",
                None,
                None,
                123,
                {"UPDATE_TAG": 123, "TENANT_ID": "tenant-id"},
                delegated_auth=True,
            )
        )

    loader.assert_called_once()


def test_delegated_app_role_assignments_continue_after_denied_application(
    monkeypatch,
) -> None:
    # Arrange
    assignment = {
        "id": "assignment-id",
        "app_role_id": None,
        "created_date_time": None,
        "principal_id": "principal-id",
        "principal_display_name": "Principal",
        "principal_type": "User",
        "resource_display_name": "Resource",
        "resource_id": "resource-id",
        "application_app_id": "visible-app",
    }

    async def get_assignments(client, neo4j_session, tenant_id, app_id):
        if app_id == "denied-app":
            raise _forbidden_error()
        yield assignment

    neo4j_session = MagicMock()
    neo4j_session.execute_read.return_value = ["denied-app", "visible-app"]
    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(app_role_assignments, "GraphServiceClient", MagicMock())
    monkeypatch.setattr(
        app_role_assignments,
        "get_app_role_assignments_for_app",
        get_assignments,
    )
    loaded_assignments = []

    def capture_assignments(session, assignments, update_tag, tenant_id):
        loaded_assignments.extend(assignments)

    loader = MagicMock(side_effect=capture_assignments)
    monkeypatch.setattr(
        app_role_assignments,
        "load_app_role_assignments",
        loader,
    )

    # Act and assert
    with pytest.raises(APIError, match="forbidden"):
        asyncio.run(
            app_role_assignments.sync_app_role_assignments(
                neo4j_session,
                "tenant-id",
                None,
                None,
                123,
                {"UPDATE_TAG": 123, "TENANT_ID": "tenant-id"},
                delegated_auth=True,
            )
        )

    loader.assert_called_once()
    assert loaded_assignments[0]["id"] == "assignment-id"
