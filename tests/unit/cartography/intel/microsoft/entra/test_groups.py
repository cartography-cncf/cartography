import asyncio
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from cartography.intel.microsoft import credentials
from cartography.intel.microsoft.entra import groups


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
    assert all(row["owner_ids"] == ["owner"] for rows in load_calls for row in rows)


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


def test_subgroup_memberships_load_after_every_group_node(monkeypatch) -> None:
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
    nested_call = next(
        i
        for i, rows in enumerate(load_calls)
        if any(row["member_group_ids"] for row in rows)
    )
    child_call = next(
        i for i, rows in enumerate(load_calls) if any(r["id"] == "child" for r in rows)
    )
    assert nested_call > child_call
    assert nested_call == len(load_calls) - 1
