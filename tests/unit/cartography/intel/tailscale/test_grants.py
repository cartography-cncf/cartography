from cartography.intel.tailscale.grants import resolve_access
from cartography.intel.tailscale.grants import transform
from cartography.intel.tailscale.utils import ACLParser


def test_aclparser_get_grants__empty_grants() -> None:
    acl = ACLParser('{"groups": {}}')
    assert acl.get_grants() == []


def test_aclparser_get_grants__empty_grants_list() -> None:
    acl = ACLParser('{"grants": []}')
    assert acl.get_grants() == []


def test_aclparser_get_grants__single_grant_user_to_tag() -> None:
    acl = ACLParser(
        '\n            {\n                "grants": [\n                    {\n                        "src": ["alice@example.com"],\n                        "dst": ["tag:web"],\n                        "ip": ["tcp:443"]\n                    }\n                ]\n            }\n            '
    )
    grants = acl.get_grants()
    assert len(grants) == 1
    grant = grants[0]
    assert grant["id"].startswith("grant:")
    assert len(grant["id"]) == len("grant:") + 12
    assert grant["sources"] == ["alice@example.com"]
    assert grant["destinations"] == ["tag:web"]
    assert grant["source_users"] == ["alice@example.com"]
    assert grant["source_groups"] == []
    assert grant["source_tags"] == []
    assert grant["destination_tags"] == ["tag:web"]
    assert grant["destination_groups"] == []
    assert grant["destination_hosts"] == []
    assert grant["ip_rules"] == ["tcp:443"]
    assert grant["app_capabilities"] == {}
    assert grant["src_posture"] == []


def test_aclparser_get_grants__group_source() -> None:
    acl = ACLParser(
        '{"grants": [{"src": ["group:eng"], "dst": ["tag:db"], "ip": ["*:*"]}]}'
    )
    grants = acl.get_grants()
    assert grants[0]["source_groups"] == ["group:eng"]
    assert grants[0]["source_users"] == []


def test_aclparser_get_grants__autogroup_source() -> None:
    acl = ACLParser(
        '{"grants": [{"src": ["autogroup:admin"], "dst": ["*"], "ip": ["*:*"]}]}'
    )
    grants = acl.get_grants()
    assert grants[0]["source_groups"] == ["autogroup:admin"]


def test_aclparser_get_grants__wildcard_source() -> None:
    acl = ACLParser('{"grants": [{"src": ["*"], "dst": ["tag:web"], "ip": ["*:*"]}]}')
    grants = acl.get_grants()
    assert grants[0]["source_any"] is True
    assert grants[0]["source_groups"] == []
    assert grants[0]["source_users"] == []


def test_aclparser_get_grants__tag_source() -> None:
    acl = ACLParser(
        '{"grants": [{"src": ["tag:server"], "dst": ["tag:db"], "ip": ["tcp:5432"]}]}'
    )
    grants = acl.get_grants()
    assert grants[0]["source_tags"] == ["tag:server"]
    assert grants[0]["source_groups"] == []
    assert grants[0]["source_users"] == []


def test_aclparser_get_grants__mixed_sources() -> None:
    acl = ACLParser(
        '\n            {\n                "grants": [{\n                    "src": ["alice@example.com", "group:eng", "tag:server", "autogroup:admin"],\n                    "dst": ["*"],\n                    "ip": ["*:*"]\n                }]\n            }\n            '
    )
    grants = acl.get_grants()
    assert grants[0]["source_users"] == ["alice@example.com"]
    assert grants[0]["source_groups"] == ["group:eng", "autogroup:admin"]
    assert grants[0]["source_tags"] == ["tag:server"]
    assert grants[0]["source_any"] is False


def test_aclparser_get_grants__tag_destination() -> None:
    acl = ACLParser(
        '{"grants": [{"src": ["*"], "dst": ["tag:web", "tag:api"], "ip": ["*:*"]}]}'
    )
    grants = acl.get_grants()
    assert grants[0]["destination_tags"] == ["tag:web", "tag:api"]


def test_aclparser_get_grants__group_destination() -> None:
    acl = ACLParser('{"grants": [{"src": ["*"], "dst": ["group:eng"], "ip": ["*:*"]}]}')
    grants = acl.get_grants()
    assert grants[0]["destination_groups"] == ["group:eng"]


def test_aclparser_get_grants__autogroup_self_destination() -> None:
    acl = ACLParser(
        '{"grants": [{"src": ["autogroup:member"], "dst": ["autogroup:self"], "ip": ["*:*"]}]}'
    )
    grants = acl.get_grants()
    assert "autogroup:self" in grants[0]["destination_groups"]


def test_aclparser_get_grants__wildcard_destination() -> None:
    acl = ACLParser('{"grants": [{"src": ["*"], "dst": ["*"], "ip": ["*:*"]}]}')
    grants = acl.get_grants()
    assert grants[0]["destination_hosts"] == ["*"]
    assert grants[0]["destination_tags"] == []
    assert grants[0]["destination_groups"] == []


def test_aclparser_get_grants__ip_rules_parsing() -> None:
    acl = ACLParser(
        '{"grants": [{"src": ["*"], "dst": ["*"], "ip": ["tcp:443", "udp:53", "tcp:8080-8090"]}]}'
    )
    grants = acl.get_grants()
    assert grants[0]["ip_rules"] == ["tcp:443", "udp:53", "tcp:8080-8090"]


def test_aclparser_get_grants__app_capabilities_parsing() -> None:
    acl = ACLParser(
        '\n            {\n                "grants": [{\n                    "src": ["group:eng"],\n                    "dst": ["tag:db"],\n                    "app": {\n                        "tailscale.com/cap/tailsql": [{"src": ["group:eng"], "db": ["prod"]}]\n                    }\n                }]\n            }\n            '
    )
    grants = acl.get_grants()
    assert grants[0]["app_capabilities"] == {
        "tailscale.com/cap/tailsql": [{"src": ["group:eng"], "db": ["prod"]}]
    }
    assert grants[0]["ip_rules"] == []


def test_aclparser_get_grants__src_posture_parsing() -> None:
    acl = ACLParser(
        '\n            {\n                "grants": [{\n                    "src": ["group:eng"],\n                    "dst": ["tag:prod"],\n                    "ip": ["*:*"],\n                    "srcPosture": ["posture:healthyDevice", "posture:managedDevice"]\n                }]\n            }\n            '
    )
    grants = acl.get_grants()
    assert grants[0]["src_posture"] == [
        "posture:healthyDevice",
        "posture:managedDevice",
    ]


def test_aclparser_get_grants__multiple_grants_have_unique_stable_ids() -> None:
    acl = ACLParser(
        '\n            {\n                "grants": [\n                    {"src": ["*"], "dst": ["*"], "ip": ["*:*"]},\n                    {"src": ["group:a"], "dst": ["tag:b"], "ip": ["tcp:80"]},\n                    {"src": ["tag:c"], "dst": ["tag:d"], "ip": ["tcp:443"]}\n                ]\n            }\n            '
    )
    grants = acl.get_grants()
    assert len(grants) == 3
    ids = [g["id"] for g in grants]
    assert len(set(ids)) == 3
    for grant_id in ids:
        assert grant_id.startswith("grant:")
        assert len(grant_id) == len("grant:") + 12


def test_aclparser_get_grants__grant_id_stable_across_reordering() -> None:
    acl1 = ACLParser(
        '\n            {\n                "grants": [\n                    {"src": ["group:a"], "dst": ["tag:b"], "ip": ["tcp:80"]},\n                    {"src": ["group:c"], "dst": ["tag:d"], "ip": ["tcp:443"]}\n                ]\n            }\n            '
    )
    acl2 = ACLParser(
        '\n            {\n                "grants": [\n                    {"src": ["group:c"], "dst": ["tag:d"], "ip": ["tcp:443"]},\n                    {"src": ["group:a"], "dst": ["tag:b"], "ip": ["tcp:80"]}\n                ]\n            }\n            '
    )
    grants1 = acl1.get_grants()
    grants2 = acl2.get_grants()
    ids1 = {g["id"] for g in grants1}
    ids2 = {g["id"] for g in grants2}
    assert ids1 == ids2


def test_aclparser_get_grants__grant_without_ip_or_app() -> None:
    acl = ACLParser('{"grants": [{"src": ["*"], "dst": ["*"]}]}')
    grants = acl.get_grants()
    assert grants[0]["ip_rules"] == []
    assert grants[0]["app_capabilities"] == {}


def test_aclparser_get_grants__comments_and_trailing_commas() -> None:
    acl = ACLParser(
        '\n            {\n                // This is a comment\n                "grants": [\n                    {\n                        // Grant for engineers\n                        "src": ["group:eng"],\n                        "dst": ["tag:web"],\n                        "ip": ["tcp:443"],\n                    },\n                ]\n            }\n            '
    )
    grants = acl.get_grants()
    assert len(grants) == 1
    assert grants[0]["source_groups"] == ["group:eng"]


def test_transform__transform_serializes_lists() -> None:
    grants = [
        {
            "id": "grant:0",
            "sources": ["group:eng"],
            "destinations": ["tag:web"],
            "source_groups": ["group:eng"],
            "source_users": [],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "ip_rules": ["tcp:443"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    result = transform(grants)
    assert result[0]["sources"] == ["group:eng"]
    assert result[0]["destinations"] == ["tag:web"]
    assert result[0]["ip_rules"] == ["tcp:443"]
    assert result[0]["app_capabilities"] is None
    assert result[0]["src_posture"] is None


def test_transform__transform_preserves_relationship_fields() -> None:
    grants = [
        {
            "id": "grant:0",
            "sources": ["alice@ex.com"],
            "destinations": ["tag:db"],
            "source_groups": [],
            "source_users": ["alice@ex.com"],
            "destination_tags": ["tag:db"],
            "destination_groups": [],
            "ip_rules": [],
            "app_capabilities": {"cap": "val"},
            "src_posture": ["posture:x"],
        }
    ]
    result = transform(grants)
    assert result[0]["source_users"] == ["alice@ex.com"]
    assert result[0]["destination_tags"] == ["tag:db"]
    assert result[0]["app_capabilities"] == '{"cap": "val"}'
    assert result[0]["src_posture"] == ["posture:x"]


DEVICES = [
    {"nodeId": "dev-1", "user": "alice@ex.com", "tags": ["tag:web"]},
    {"nodeId": "dev-2", "user": "alice@ex.com", "tags": []},
    {"nodeId": "dev-3", "user": "bob@ex.com", "tags": ["tag:db"]},
    {"nodeId": "dev-4", "user": "bob@ex.com", "tags": ["tag:web", "tag:db"]},
]
GROUPS = [
    {"id": "group:eng", "members": ["alice@ex.com", "bob@ex.com"], "sub_groups": []},
    {"id": "group:admin", "members": ["alice@ex.com"], "sub_groups": []},
    {
        "id": "autogroup:member",
        "members": ["alice@ex.com", "bob@ex.com"],
        "sub_groups": [],
    },
    {"id": "group:all", "members": [], "sub_groups": ["group:eng"]},
]
USERS = [{"loginName": "alice@ex.com"}, {"loginName": "bob@ex.com"}]


def test_resolve_access_direct_user__user_to_tag_destination() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": ["tcp:443"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, group_access, device_access, _, _ = resolve_access(
        grants, DEVICES, GROUPS, [], USERS
    )
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {("alice@ex.com", "dev-1"), ("alice@ex.com", "dev-4")}
    assert group_access == []
    device_pairs = {(a["source_device_id"], a["device_id"]) for a in device_access}
    assert ("dev-2", "dev-1") in device_pairs
    assert ("dev-2", "dev-4") in device_pairs
    assert ("dev-1", "dev-4") in device_pairs
    for src, dst in device_pairs:
        assert src != dst


def test_resolve_access_direct_user__user_to_wildcard_destination() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["*"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_hosts": ["*"],
            "ip_rules": ["*:*"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {
        ("alice@ex.com", "dev-1"),
        ("alice@ex.com", "dev-2"),
        ("alice@ex.com", "dev-3"),
        ("alice@ex.com", "dev-4"),
    }


def test_resolve_access_direct_user__unknown_user_ignored() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["unknown@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["*"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_hosts": ["*"],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    assert user_access == []


def test_resolve_access_direct_user__user_to_autogroup_self() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["autogroup:self"],
            "destination_tags": [],
            "destination_groups": ["autogroup:self"],
            "destination_hosts": [],
            "ip_rules": ["*:*"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {("alice@ex.com", "dev-1"), ("alice@ex.com", "dev-2")}


def test_resolve_access_direct_user__wildcard_source_expands_to_all_users() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": [],
            "source_tags": [],
            "source_any": True,
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": ["*:*"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    user_logins = {a["user_login_name"] for a in user_access}
    assert user_logins == {"alice@ex.com", "bob@ex.com"}


def test_resolve_access_group__group_to_tag_destination() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": ["group:admin"],
            "source_tags": [],
            "destinations": ["tag:db"],
            "destination_tags": ["tag:db"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": ["tcp:5432"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, group_access, _, _, _ = resolve_access(
        grants, DEVICES, GROUPS, [], USERS
    )
    group_pairs = {(a["group_id"], a["device_id"]) for a in group_access}
    assert group_pairs == {("group:admin", "dev-3"), ("group:admin", "dev-4")}
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {("alice@ex.com", "dev-3"), ("alice@ex.com", "dev-4")}


def test_resolve_access_group__group_to_autogroup_self() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": ["group:eng"],
            "source_tags": [],
            "destinations": ["autogroup:self"],
            "destination_tags": [],
            "destination_groups": ["autogroup:self"],
            "destination_hosts": [],
            "ip_rules": ["*:*"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {
        ("alice@ex.com", "dev-1"),
        ("alice@ex.com", "dev-2"),
        ("bob@ex.com", "dev-3"),
        ("bob@ex.com", "dev-4"),
    }


def test_resolve_access_group__group_destination_resolves_to_member_devices() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["group:admin"],
            "destination_tags": [],
            "destination_groups": ["group:admin"],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {("alice@ex.com", "dev-1"), ("alice@ex.com", "dev-2")}


def test_resolve_access_group__transitive_group_members_are_used() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": ["group:all"],
            "source_tags": [],
            "destinations": ["tag:db"],
            "destination_tags": ["tag:db"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    groups = [
        (
            {
                **group,
                "effective_members": ["alice@ex.com", "bob@ex.com"],
            }
            if group["id"] == "group:all"
            else group
        )
        for group in GROUPS
    ]
    user_access, group_access, _, _, _ = resolve_access(
        grants, DEVICES, groups, [], USERS
    )
    group_pairs = {(a["group_id"], a["device_id"]) for a in group_access}
    assert group_pairs == {("group:all", "dev-3"), ("group:all", "dev-4")}
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {
        ("alice@ex.com", "dev-3"),
        ("alice@ex.com", "dev-4"),
        ("bob@ex.com", "dev-3"),
        ("bob@ex.com", "dev-4"),
    }


def test_resolve_access_tag_source__tag_source_to_tag_destination() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": [],
            "source_tags": ["tag:web"],
            "destinations": ["tag:db"],
            "destination_tags": ["tag:db"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": ["tcp:5432"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, device_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    device_pairs = {(a["source_device_id"], a["device_id"]) for a in device_access}
    assert device_pairs == {("dev-1", "dev-3"), ("dev-1", "dev-4"), ("dev-4", "dev-3")}


def test_resolve_access_tag_source__tag_source_to_wildcard() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": [],
            "source_tags": ["tag:db"],
            "destinations": ["*"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_hosts": ["*"],
            "ip_rules": ["*:*"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, device_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    device_pairs = {(a["source_device_id"], a["device_id"]) for a in device_access}
    assert device_pairs == {
        ("dev-3", "dev-1"),
        ("dev-3", "dev-2"),
        ("dev-3", "dev-4"),
        ("dev-4", "dev-1"),
        ("dev-4", "dev-2"),
        ("dev-4", "dev-3"),
    }


def test_resolve_access_tag_source__tag_source_no_self_loops() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": [],
            "source_tags": ["tag:web"],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, device_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    for entry in device_access:
        assert entry["source_device_id"] != entry["device_id"]


def test_resolve_access_deduplication__multiple_grants_aggregated() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": ["tcp:80"],
            "app_capabilities": {},
            "src_posture": [],
        },
        {
            "id": "grant:1",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": ["tcp:443"],
            "app_capabilities": {},
            "src_posture": [],
        },
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    for entry in user_access:
        if entry["user_login_name"] == "alice@ex.com":
            assert entry["granted_by"] == ["grant:0", "grant:1"]


def test_resolve_access_deduplication__user_via_direct_and_group_aggregated() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": ["group:admin"],
            "source_tags": [],
            "destinations": ["tag:db"],
            "destination_tags": ["tag:db"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    alice_entries = [a for a in user_access if a["user_login_name"] == "alice@ex.com"]
    for entry in alice_entries:
        assert entry["granted_by"] == ["grant:0"]


def test_resolve_access_deduplication__same_grant_not_duplicated_in_granted_by() -> (
    None
):
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": ["group:admin"],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    alice_dev1 = [
        a
        for a in user_access
        if a["user_login_name"] == "alice@ex.com" and a["device_id"] == "dev-1"
    ]
    assert len(alice_dev1) == 1
    assert alice_dev1[0]["granted_by"] == ["grant:0"]


def test_resolve_access_edge_cases__empty_grants() -> None:
    user_access, group_access, device_access, _, _ = resolve_access(
        [], DEVICES, GROUPS, [], USERS
    )
    assert user_access == []
    assert group_access == []
    assert device_access == []


def test_resolve_access_edge_cases__grant_with_no_matching_destination() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:nonexistent"],
            "destination_tags": ["tag:nonexistent"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    assert user_access == []


def test_resolve_access_edge_cases__app_only_grant_does_not_create_can_access() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {"tailscale.com/cap/test": [{"x": "y"}]},
            "src_posture": [],
        }
    ]
    user_access, group_access, device_access, user_svc_access, group_svc_access = (
        resolve_access(grants, DEVICES, GROUPS, [], USERS)
    )
    assert user_access == []
    assert group_access == []
    assert device_access == []
    assert user_svc_access == []
    assert group_svc_access == []


def test_resolve_access_edge_cases__grant_ip_rules_stored_on_relationship() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": ["tcp:443", "tcp:8080"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    assert user_access[0]["granted_by"] == ["grant:0"]


def test_resolve_access_edge_cases__grant_without_ip_rules() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["*"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_hosts": ["*"],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    assert user_access[0]["granted_by"] == ["grant:0"]


def test_resolve_access_edge_cases__tag_destination_with_port_suffix_stripped() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web:443"],
            "destination_tags": ["tag:web:443"],
            "destination_groups": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {("alice@ex.com", "dev-1"), ("alice@ex.com", "dev-4")}


SERVICES = [{"name": "web-server"}, {"name": "database"}]
SERVICES_WITH_PREFIX = [{"name": "svc:web-server"}, {"name": "svc:database"}]


def test_aclparser_service_destination__svc_destination_classified() -> None:
    acl = ACLParser(
        '{"grants": [{"src": ["group:eng"], "dst": ["svc:web-server"], "ip": ["tcp:443"]}]}'
    )
    grants = acl.get_grants()
    assert grants[0]["destination_services"] == ["svc:web-server"]
    assert grants[0]["destination_tags"] == []
    assert grants[0]["destination_hosts"] == []


def test_aclparser_service_destination__mixed_svc_and_tag_destinations() -> None:
    acl = ACLParser(
        '{"grants": [{"src": ["*"], "dst": ["svc:db", "tag:web"], "ip": ["*:*"]}]}'
    )
    grants = acl.get_grants()
    assert grants[0]["destination_services"] == ["svc:db"]
    assert grants[0]["destination_tags"] == ["tag:web"]


def test_resolve_access_service_destination__user_to_service() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["svc:web-server"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": ["svc:web-server"],
            "destination_hosts": [],
            "ip_rules": ["tcp:443"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, _, user_svc, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS, SERVICES)
    svc_pairs = {(a["user_login_name"], a["service_id"]) for a in user_svc}
    assert svc_pairs == {("alice@ex.com", "svc:web-server")}


def test_resolve_access_service_destination__group_to_service() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": ["group:admin"],
            "source_tags": [],
            "destinations": ["svc:database"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": ["svc:database"],
            "destination_hosts": [],
            "ip_rules": ["tcp:5432"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, _, user_svc, group_svc = resolve_access(
        grants, DEVICES, GROUPS, [], USERS, SERVICES
    )
    group_pairs = {(a["group_id"], a["service_id"]) for a in group_svc}
    assert group_pairs == {("group:admin", "svc:database")}
    user_pairs = {(a["user_login_name"], a["service_id"]) for a in user_svc}
    assert user_pairs == {("alice@ex.com", "svc:database")}


def test_resolve_access_service_destination__unknown_service_ignored() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["svc:nonexistent"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": ["svc:nonexistent"],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, _, user_svc, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS, SERVICES)
    assert user_svc == []


def test_resolve_access_service_destination__mixed_device_and_service_destinations() -> (
    None
):
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web", "svc:database"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_services": ["svc:database"],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, user_svc, _ = resolve_access(
        grants, DEVICES, GROUPS, [], USERS, SERVICES
    )
    device_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert ("alice@ex.com", "dev-1") in device_pairs
    svc_pairs = {(a["user_login_name"], a["service_id"]) for a in user_svc}
    assert svc_pairs == {("alice@ex.com", "svc:database")}


def test_resolve_access_service_destination__prefixed_service_names_supported() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "source_any": False,
            "destinations": ["svc:web-server"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": ["svc:web-server"],
            "destination_hosts": [],
            "ip_rules": ["tcp:443"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, _, user_svc, _ = resolve_access(
        grants, DEVICES, GROUPS, [], USERS, SERVICES_WITH_PREFIX
    )
    assert {(a["user_login_name"], a["service_id"]) for a in user_svc} == {
        ("alice@ex.com", "svc:web-server")
    }


DEVICES_WITH_IPS = [
    {
        "nodeId": "dev-1",
        "user": "alice@ex.com",
        "tags": [],
        "addresses": ["100.64.0.1", "fd7a:115c:a1e0::1"],
    },
    {
        "nodeId": "dev-2",
        "user": "alice@ex.com",
        "tags": [],
        "addresses": ["100.64.0.2"],
    },
    {"nodeId": "dev-3", "user": "bob@ex.com", "tags": [], "addresses": ["100.64.1.10"]},
    {"nodeId": "dev-4", "user": "bob@ex.com", "tags": [], "addresses": []},
]


def test_resolve_access_ipdestination__exact_ip_destination() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["100.64.0.1"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": ["100.64.0.1"],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES_WITH_IPS, GROUPS, [], USERS
    )
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {("alice@ex.com", "dev-1")}


def test_resolve_access_ipdestination__cidr_destination() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["100.64.0.0/24"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": ["100.64.0.0/24"],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES_WITH_IPS, GROUPS, [], USERS
    )
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {("alice@ex.com", "dev-1"), ("alice@ex.com", "dev-2")}


def test_resolve_access_ipdestination__cidr_slash32_destination() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["100.64.1.10/32"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": ["100.64.1.10/32"],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES_WITH_IPS, GROUPS, [], USERS
    )
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {("alice@ex.com", "dev-3")}


def test_resolve_access_ipdestination__ipv6_destination() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["fd7a:115c:a1e0::1"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": ["fd7a:115c:a1e0::1"],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES_WITH_IPS, GROUPS, [], USERS
    )
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {("alice@ex.com", "dev-1")}


def test_resolve_access_ipdestination__nonexistent_ip_ignored() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["10.0.0.99"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": ["10.0.0.99"],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES_WITH_IPS, GROUPS, [], USERS
    )
    assert user_access == []


def test_resolve_access_ipdestination__invalid_destination_ignored() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["not-an-ip-or-selector"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": ["not-an-ip-or-selector"],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES_WITH_IPS, GROUPS, [], USERS
    )
    assert user_access == []


def test_resolve_access_ipdestination__unsupported_destination_logs_warning(
    caplog,
) -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["ipset:corp"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": ["ipset:corp"],
            "ip_rules": ["*:*"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    resolve_access(grants, DEVICES_WITH_IPS, GROUPS, [], USERS)
    assert (
        "Unsupported Tailscale grant destination selector 'ipset:corp'" in caplog.text
    )


def test_resolve_access_ipdestination__valid_unmatched_cidr_does_not_warn(
    caplog,
) -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["10.0.0.0/24"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": ["10.0.0.0/24"],
            "ip_rules": ["*:*"],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES_WITH_IPS, GROUPS, [], USERS
    )
    assert user_access == []
    assert (
        "Unsupported Tailscale grant destination selector '10.0.0.0/24'"
        not in caplog.text
    )


def test_resolve_access_ipdestination__wide_cidr_matches_all() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["100.0.0.0/8"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": ["100.0.0.0/8"],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES_WITH_IPS, GROUPS, [], USERS
    )
    user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
    assert user_pairs == {
        ("alice@ex.com", "dev-1"),
        ("alice@ex.com", "dev-2"),
        ("alice@ex.com", "dev-3"),
    }


POSTURE_MATCHES = [
    {"device_id": "dev-1", "posture_id": "posture:healthy"},
    {"device_id": "dev-3", "posture_id": "posture:healthy"},
    {"device_id": "dev-3", "posture_id": "posture:managed"},
]


def test_resolve_access_posture_filtering__no_posture_no_filtering() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com", "bob@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES, GROUPS, [], USERS, [], POSTURE_MATCHES
    )
    user_logins = {a["user_login_name"] for a in user_access}
    assert "alice@ex.com" in user_logins
    assert "bob@ex.com" in user_logins


def test_resolve_access_posture_filtering__posture_filters_non_compliant_user() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com", "bob@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": ["posture:managed"],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES, GROUPS, [], USERS, [], POSTURE_MATCHES
    )
    user_logins = {a["user_login_name"] for a in user_access}
    assert "bob@ex.com" in user_logins
    assert "alice@ex.com" not in user_logins


def test_resolve_access_posture_filtering__posture_requires_all_postures() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com", "bob@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": ["posture:healthy", "posture:managed"],
        }
    ]
    user_access, _, _, _, _ = resolve_access(
        grants, DEVICES, GROUPS, [], USERS, [], POSTURE_MATCHES
    )
    user_logins = {a["user_login_name"] for a in user_access}
    assert "bob@ex.com" in user_logins
    assert "alice@ex.com" not in user_logins


def test_resolve_access_posture_filtering__posture_filters_group_members() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": ["group:eng"],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": ["posture:managed"],
        }
    ]
    user_access, group_access, _, _, _ = resolve_access(
        grants, DEVICES, GROUPS, [], USERS, [], POSTURE_MATCHES
    )
    group_pairs = {(a["group_id"], a["device_id"]) for a in group_access}
    assert len(group_pairs) > 0
    user_logins = {a["user_login_name"] for a in user_access}
    assert "bob@ex.com" in user_logins
    assert "alice@ex.com" not in user_logins


def test_resolve_access_posture_filtering__posture_filters_device_sources() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": [],
            "source_tags": ["tag:web"],
            "destinations": ["tag:db"],
            "destination_tags": ["tag:db"],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": ["posture:healthy"],
        }
    ]
    _, _, device_access, _, _ = resolve_access(
        grants, DEVICES, GROUPS, [], USERS, [], POSTURE_MATCHES
    )
    source_ids = {a["source_device_id"] for a in device_access}
    assert "dev-1" in source_ids
    assert "dev-4" not in source_ids


def test_resolve_access_posture_filtering__no_posture_matches_blocks_all_with_posture_requirement() -> (
    None
):
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": ["posture:healthy"],
        }
    ]
    user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS, [], [])
    assert user_access == []


def test_resolve_access_user_device_propagation__user_access_propagated_to_devices() -> (
    None
):
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:db"],
            "destination_tags": ["tag:db"],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, device_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    device_pairs = {(a["source_device_id"], a["device_id"]) for a in device_access}
    assert ("dev-1", "dev-3") in device_pairs
    assert ("dev-1", "dev-4") in device_pairs
    assert ("dev-2", "dev-3") in device_pairs
    assert ("dev-2", "dev-4") in device_pairs


def test_resolve_access_user_device_propagation__propagation_no_self_loops() -> None:
    grants = [
        {
            "id": "grant:0",
            "source_users": ["alice@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["*"],
            "destination_tags": [],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": ["*"],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, device_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    for entry in device_access:
        assert entry["source_device_id"] != entry["device_id"]


def test_resolve_access_user_device_propagation__propagation_carries_granted_by() -> (
    None
):
    grants = [
        {
            "id": "grant:0",
            "source_users": ["bob@ex.com"],
            "source_groups": [],
            "source_tags": [],
            "destinations": ["tag:web"],
            "destination_tags": ["tag:web"],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, device_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    bob_dev3_to_dev1 = [
        a
        for a in device_access
        if a["source_device_id"] == "dev-3" and a["device_id"] == "dev-1"
    ]
    assert len(bob_dev3_to_dev1) == 1
    assert "grant:0" in bob_dev3_to_dev1[0]["granted_by"]


def test_resolve_access_user_device_propagation__group_user_access_also_propagated() -> (
    None
):
    grants = [
        {
            "id": "grant:0",
            "source_users": [],
            "source_groups": ["group:admin"],
            "source_tags": [],
            "destinations": ["tag:db"],
            "destination_tags": ["tag:db"],
            "destination_groups": [],
            "destination_services": [],
            "destination_hosts": [],
            "ip_rules": [],
            "app_capabilities": {},
            "src_posture": [],
        }
    ]
    _, _, device_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
    device_pairs = {(a["source_device_id"], a["device_id"]) for a in device_access}
    assert ("dev-1", "dev-3") in device_pairs
    assert ("dev-2", "dev-4") in device_pairs
