import asyncio
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from msgraph.generated.models.o_data_errors.main_error import MainError
from msgraph.generated.models.o_data_errors.o_data_error import ODataError

from cartography.intel.microsoft import credentials
from cartography.intel.microsoft.entra import groups
from cartography.intel.microsoft.entra.groups import get_group_member_pages
from tests.data.microsoft.entra.groups import MOCK_GROUP_MEMBERS


class MockPage:
    def __init__(self, value, odata_next_link=None):
        self.value = value
        self.odata_next_link = odata_next_link


def _expired_page_token_error() -> ODataError:
    error = ODataError()
    error.response_status_code = 400
    error.error = MainError()
    error.error.code = "Directory_ExpiredPageToken"
    error.error.message = (
        "The specified page token value has expired and can no longer be "
        "included in your request."
    )
    return error


class MockGroupMembersRequestBuilder:
    def __init__(self, first_page, second_page, recover_on_second_attempt=True):
        self.first_page = first_page
        self.second_page = second_page
        self.recover_on_second_attempt = recover_on_second_attempt
        self.first_page_calls = 0
        self.next_page_calls = 0
        self.expired_token_raised = False

    async def get(self, request_configuration=None):
        self.first_page_calls += 1
        self.request_configuration = request_configuration
        return self.first_page

    def with_url(self, next_link):
        assert next_link == "next-page"
        return MockGroupMembersNextPageRequestBuilder(self)


class MockGroupMembersNextPageRequestBuilder:
    def __init__(self, parent):
        self.parent = parent

    async def get(self):
        self.parent.next_page_calls += 1
        if (
            not self.parent.expired_token_raised
            or not self.parent.recover_on_second_attempt
        ):
            self.parent.expired_token_raised = True
            raise _expired_page_token_error()
        return self.parent.second_page


class MockGroupsRequestBuilder:
    def __init__(self, members_builder):
        self.members_builder = members_builder

    def by_group_id(self, group_id):
        return MockGroupRequestBuilder(self.members_builder)


class MockGroupRequestBuilder:
    def __init__(self, members_builder):
        self.members = members_builder


class MockGraphClient:
    def __init__(self, members_builder):
        self.groups = MockGroupsRequestBuilder(members_builder)


def _sync_groups(monkeypatch, group_list, member_pages_by_group) -> list[list[Any]]:
    async def get_groups(client):
        for group in group_list:
            yield group

    async def get_member_pages(client, group_id):
        for page in member_pages_by_group.get(group_id, []):
            yield page

    load_calls: list[list[Any]] = []
    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(groups, "GraphServiceClient", MagicMock())
    monkeypatch.setattr(groups, "get_entra_groups", get_groups)
    monkeypatch.setattr(groups, "get_group_owners", AsyncMock(return_value=["owner"]))
    monkeypatch.setattr(groups, "get_group_member_pages", get_member_pages)
    monkeypatch.setattr(
        groups,
        "load_groups",
        lambda session, rows, update_tag, tenant_id: load_calls.append(rows),
    )
    monkeypatch.setattr(groups, "cleanup_groups", MagicMock())

    asyncio.run(
        groups.sync_entra_groups(
            MagicMock(),
            "tenant-id",
            "client-id",
            "client-secret",
            123,
            {"UPDATE_TAG": 123, "TENANT_ID": "tenant-id"},
        )
    )
    return load_calls


def test_large_group_membership_is_loaded_across_bounded_flushes(monkeypatch) -> None:
    # Arrange
    monkeypatch.setattr(groups, "PENDING_MEMBERSHIP_LIMIT", 5)
    big = MagicMock(id="big", display_name="Everyone")
    small = MagicMock(id="small", display_name="Admins")
    big_pages: list[tuple[list[str], list[str]]] = [
        ([f"user-{page}-{i}" for i in range(3)], []) for page in range(4)
    ]
    member_pages = {
        "big": big_pages,
        "small": [(["admin"], ["big"])],
    }

    # Act
    load_calls = _sync_groups(monkeypatch, [big, small], member_pages)

    # Assert
    assert len(load_calls) > 1
    for rows in load_calls:
        pending = sum(
            len(row["member_ids"]) + len(row["member_group_ids"]) for row in rows
        )
        assert pending <= 5 + 3
    loaded_members = {
        (row["id"], member)
        for rows in load_calls
        for row in rows
        for member in row["member_ids"] + row["member_group_ids"]
    }
    expected = {("big", user) for users, _ in big_pages for user in users}
    expected |= {("small", "admin"), ("small", "big")}
    assert loaded_members == expected
    assert {row["id"] for row in load_calls[0]} == {"big", "small"}
    assert all(row["owner_ids"] == ["owner"] for row in load_calls[0])


def test_group_without_members_is_still_loaded(monkeypatch) -> None:
    # Arrange
    empty = MagicMock(id="empty", display_name="Empty")

    # Act
    load_calls = _sync_groups(monkeypatch, [empty], {})

    # Assert
    assert len(load_calls) == 1
    (row,) = load_calls[0]
    assert row["id"] == "empty"
    assert row["member_ids"] == []
    assert row["member_group_ids"] == []
    assert row["owner_ids"] == ["owner"]


def test_every_group_node_loads_before_any_membership(monkeypatch) -> None:
    # Arrange: Graph lists the parent before the group nested in it.
    monkeypatch.setattr(groups, "PENDING_MEMBERSHIP_LIMIT", 1)
    parent = MagicMock(id="parent", display_name="Parent")
    child = MagicMock(id="child", display_name="Child")
    member_pages = {
        "parent": [(["user-a"], ["child"])],
        "child": [(["user-b"], [])],
    }

    # Act
    load_calls = _sync_groups(monkeypatch, [parent, child], member_pages)

    # Assert
    node_rows, *membership_loads = load_calls
    assert {row["id"] for row in node_rows} == {"parent", "child"}
    assert all(
        not row["member_ids"] and not row["member_group_ids"] for row in node_rows
    )
    assert ("parent", ["child"]) in [
        (row["id"], row["member_group_ids"])
        for rows in membership_loads
        for row in rows
    ]


@pytest.mark.asyncio
async def test_get_group_member_pages_restarts_after_expired_page_token():
    first_page = MockPage(
        [
            MOCK_GROUP_MEMBERS["11111111-1111-1111-1111-111111111111"][0],
        ],
        "next-page",
    )
    second_page = MockPage(
        [
            MOCK_GROUP_MEMBERS["11111111-1111-1111-1111-111111111111"][1],
            MOCK_GROUP_MEMBERS["11111111-1111-1111-1111-111111111111"][2],
        ],
    )
    members_builder = MockGroupMembersRequestBuilder(first_page, second_page)
    client = MockGraphClient(members_builder)

    pages = [
        page
        async for page in get_group_member_pages(
            client,
            "11111111-1111-1111-1111-111111111111",
        )
    ]

    # The restart re-yields the first page; the group load is an idempotent MERGE.
    assert pages == [
        (["ae4ac864-4433-4ba6-96a6-20f8cffdadcb"], []),
        (["ae4ac864-4433-4ba6-96a6-20f8cffdadcb"], []),
        (
            ["11dca63b-cb03-4e53-bb75-fa8060285550"],
            ["22222222-2222-2222-2222-222222222222"],
        ),
    ]
    query = members_builder.request_configuration.query_parameters
    assert query.select == ["id"]
    assert query.top == 999
    assert members_builder.first_page_calls == 2
    assert members_builder.next_page_calls == 2


@pytest.mark.asyncio
async def test_get_group_member_pages_does_not_restart_expired_page_token_forever():
    first_page = MockPage(
        [
            MOCK_GROUP_MEMBERS["11111111-1111-1111-1111-111111111111"][0],
        ],
        "next-page",
    )
    second_page = MockPage([])
    members_builder = MockGroupMembersRequestBuilder(
        first_page,
        second_page,
        recover_on_second_attempt=False,
    )
    client = MockGraphClient(members_builder)

    with pytest.raises(ODataError):
        async for _ in get_group_member_pages(
            client,
            "11111111-1111-1111-1111-111111111111",
        ):
            pass

    assert members_builder.first_page_calls == 6
    assert members_builder.next_page_calls == 6


@pytest.mark.asyncio
async def test_get_group_member_pages_yields_nothing_for_missing_first_page():
    members_builder = MockGroupMembersRequestBuilder(None, MockPage([]))
    client = MockGraphClient(members_builder)

    pages = [
        page
        async for page in get_group_member_pages(
            client,
            "11111111-1111-1111-1111-111111111111",
        )
    ]

    assert pages == []
    assert members_builder.first_page_calls == 1
    assert members_builder.next_page_calls == 0
