from cartography.intel.tailscale.acls import build_effective_group_members
from cartography.intel.tailscale.acls import build_inherited_member_relationships


def test_build_effective_group_members_handles_cycles() -> None:
    groups = [
        {
            "id": "group:a",
            "members": ["a@example.com"],
            "sub_groups": ["group:b"],
        },
        {
            "id": "group:b",
            "members": ["b@example.com"],
            "sub_groups": ["group:a"],
        },
    ]

    result = build_effective_group_members(groups)

    assert result == {
        "group:a": {"a@example.com", "b@example.com"},
        "group:b": {"a@example.com", "b@example.com"},
    }


def test_build_inherited_member_relationships_handles_cycles() -> None:
    groups = [
        {
            "id": "group:a",
            "members": ["a@example.com"],
            "sub_groups": ["group:b"],
        },
        {
            "id": "group:b",
            "members": ["b@example.com"],
            "sub_groups": ["group:a"],
        },
    ]

    result = {
        (row["user_login_name"], row["group_id"])
        for row in build_inherited_member_relationships(groups)
    }

    assert result == {
        ("a@example.com", "group:a"),
        ("b@example.com", "group:a"),
        ("a@example.com", "group:b"),
        ("b@example.com", "group:b"),
    }
