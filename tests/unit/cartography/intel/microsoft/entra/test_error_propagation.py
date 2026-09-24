import asyncio
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

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


def _forbidden_error() -> APIError:
    error = APIError("forbidden")
    error.response_status_code = 403
    return error


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
) -> None:
    # Arrange
    async def get_users_then_deny(client):
        yield MagicMock(id="visible-user")
        raise _forbidden_error()

    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(users, "GraphServiceClient", MagicMock())
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
    get_members = AsyncMock(side_effect=[(["member-id"], []), ([], [])])
    graph_client = MagicMock()
    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(
        groups, "GraphServiceClient", MagicMock(return_value=graph_client)
    )
    monkeypatch.setattr(groups, "get_entra_groups", get_groups)
    monkeypatch.setattr(groups, "get_group_owners", get_owners)
    monkeypatch.setattr(groups, "get_group_members", get_members)
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

    load_groups.assert_called_once()
    loaded_groups = load_groups.call_args.args[1]
    assert {group["id"] for group in loaded_groups} == {
        "denied-group",
        "visible-group",
    }
    denied = next(group for group in loaded_groups if group["id"] == "denied-group")
    assert denied["owner_ids"] == []
    assert denied["member_ids"] == ["member-id"]
    assert get_members.await_count == 2


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
    monkeypatch.setattr(
        groups,
        "get_group_members",
        AsyncMock(side_effect=_forbidden_error()),
    )
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
    monkeypatch.setattr(module, "GraphServiceClient", MagicMock())
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
