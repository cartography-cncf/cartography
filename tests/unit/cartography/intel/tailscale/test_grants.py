"""Unit tests for Tailscale grants parsing and access resolution.

Covers:
- ACLParser.get_grants() parsing for all source/destination selector types
- resolve_access() for all P1 cases:
  - Direct user sources
  - Group/autogroup sources
  - Tag sources (device-to-device)
  - autogroup:self destinations
  - Wildcard sources and destinations
  - Mixed capabilities (ip, app, srcPosture)
- Edge cases: empty grants, unknown users, self-loops, deduplication
"""

import json

from cartography.intel.tailscale.grants import resolve_access
from cartography.intel.tailscale.grants import transform
from cartography.intel.tailscale.utils import ACLParser

# ============================================================================
# ACLParser.get_grants() tests
# ============================================================================


class TestACLParserGetGrants:
    """Tests for ACLParser.get_grants() parsing logic."""

    def test_empty_grants(self) -> None:
        """No grants section returns empty list."""
        acl = ACLParser('{"groups": {}}')
        assert acl.get_grants() == []

    def test_empty_grants_list(self) -> None:
        """Empty grants array returns empty list."""
        acl = ACLParser('{"grants": []}')
        assert acl.get_grants() == []

    def test_single_grant_user_to_tag(self) -> None:
        """Parse a simple user -> tag grant."""
        acl = ACLParser(
            """
            {
                "grants": [
                    {
                        "src": ["alice@example.com"],
                        "dst": ["tag:web"],
                        "ip": ["tcp:443"]
                    }
                ]
            }
            """,
        )
        grants = acl.get_grants()
        assert len(grants) == 1
        grant = grants[0]
        assert grant["id"] == "grant:0"
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

    def test_group_source(self) -> None:
        """Groups in src are classified as source_groups."""
        acl = ACLParser(
            '{"grants": [{"src": ["group:eng"], "dst": ["tag:db"], "ip": ["*:*"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["source_groups"] == ["group:eng"]
        assert grants[0]["source_users"] == []

    def test_autogroup_source(self) -> None:
        """Autogroups in src are classified as source_groups."""
        acl = ACLParser(
            '{"grants": [{"src": ["autogroup:admin"], "dst": ["*"], "ip": ["*:*"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["source_groups"] == ["autogroup:admin"]

    def test_wildcard_source(self) -> None:
        """Wildcard * in src is mapped to autogroup:member."""
        acl = ACLParser(
            '{"grants": [{"src": ["*"], "dst": ["tag:web"], "ip": ["*:*"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["source_groups"] == ["autogroup:member"]
        assert grants[0]["source_users"] == []

    def test_tag_source(self) -> None:
        """Tags in src are classified as source_tags."""
        acl = ACLParser(
            '{"grants": [{"src": ["tag:server"], "dst": ["tag:db"], "ip": ["tcp:5432"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["source_tags"] == ["tag:server"]
        assert grants[0]["source_groups"] == []
        assert grants[0]["source_users"] == []

    def test_mixed_sources(self) -> None:
        """Multiple source types are classified correctly."""
        acl = ACLParser(
            """
            {
                "grants": [{
                    "src": ["alice@example.com", "group:eng", "tag:server", "autogroup:admin"],
                    "dst": ["*"],
                    "ip": ["*:*"]
                }]
            }
            """,
        )
        grants = acl.get_grants()
        assert grants[0]["source_users"] == ["alice@example.com"]
        assert grants[0]["source_groups"] == ["group:eng", "autogroup:admin"]
        assert grants[0]["source_tags"] == ["tag:server"]

    def test_tag_destination(self) -> None:
        """Tags in dst are classified as destination_tags."""
        acl = ACLParser(
            '{"grants": [{"src": ["*"], "dst": ["tag:web", "tag:api"], "ip": ["*:*"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["destination_tags"] == ["tag:web", "tag:api"]

    def test_group_destination(self) -> None:
        """Groups in dst are classified as destination_groups."""
        acl = ACLParser(
            '{"grants": [{"src": ["*"], "dst": ["group:eng"], "ip": ["*:*"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["destination_groups"] == ["group:eng"]

    def test_autogroup_self_destination(self) -> None:
        """autogroup:self in dst is classified as destination_hosts (not group)."""
        acl = ACLParser(
            '{"grants": [{"src": ["autogroup:member"], "dst": ["autogroup:self"], "ip": ["*:*"]}]}',
        )
        grants = acl.get_grants()
        # autogroup:self doesn't start with "group:" so it goes to destination_hosts
        # but it does start with "autogroup:" so it goes to destination_groups
        assert "autogroup:self" in grants[0]["destination_groups"]

    def test_wildcard_destination(self) -> None:
        """Wildcard * in dst is classified as destination_hosts."""
        acl = ACLParser(
            '{"grants": [{"src": ["*"], "dst": ["*"], "ip": ["*:*"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["destination_hosts"] == ["*"]
        assert grants[0]["destination_tags"] == []
        assert grants[0]["destination_groups"] == []

    def test_ip_rules_parsing(self) -> None:
        """IP rules are parsed correctly."""
        acl = ACLParser(
            '{"grants": [{"src": ["*"], "dst": ["*"], "ip": ["tcp:443", "udp:53", "tcp:8080-8090"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["ip_rules"] == ["tcp:443", "udp:53", "tcp:8080-8090"]

    def test_app_capabilities_parsing(self) -> None:
        """App capabilities are parsed correctly."""
        acl = ACLParser(
            """
            {
                "grants": [{
                    "src": ["group:eng"],
                    "dst": ["tag:db"],
                    "app": {
                        "tailscale.com/cap/tailsql": [{"src": ["group:eng"], "db": ["prod"]}]
                    }
                }]
            }
            """,
        )
        grants = acl.get_grants()
        assert grants[0]["app_capabilities"] == {
            "tailscale.com/cap/tailsql": [{"src": ["group:eng"], "db": ["prod"]}],
        }
        assert grants[0]["ip_rules"] == []

    def test_src_posture_parsing(self) -> None:
        """srcPosture is parsed correctly."""
        acl = ACLParser(
            """
            {
                "grants": [{
                    "src": ["group:eng"],
                    "dst": ["tag:prod"],
                    "ip": ["*:*"],
                    "srcPosture": ["posture:healthyDevice", "posture:managedDevice"]
                }]
            }
            """,
        )
        grants = acl.get_grants()
        assert grants[0]["src_posture"] == [
            "posture:healthyDevice",
            "posture:managedDevice",
        ]

    def test_multiple_grants_indexed(self) -> None:
        """Multiple grants get sequential IDs."""
        acl = ACLParser(
            """
            {
                "grants": [
                    {"src": ["*"], "dst": ["*"], "ip": ["*:*"]},
                    {"src": ["group:a"], "dst": ["tag:b"], "ip": ["tcp:80"]},
                    {"src": ["tag:c"], "dst": ["tag:d"], "ip": ["tcp:443"]}
                ]
            }
            """,
        )
        grants = acl.get_grants()
        assert len(grants) == 3
        assert grants[0]["id"] == "grant:0"
        assert grants[1]["id"] == "grant:1"
        assert grants[2]["id"] == "grant:2"

    def test_grant_without_ip_or_app(self) -> None:
        """Grant with neither ip nor app still parses (both default to empty)."""
        acl = ACLParser(
            '{"grants": [{"src": ["*"], "dst": ["*"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["ip_rules"] == []
        assert grants[0]["app_capabilities"] == {}

    def test_comments_and_trailing_commas(self) -> None:
        """Parser handles Tailscale-style comments and trailing commas."""
        acl = ACLParser(
            """
            {
                // This is a comment
                "grants": [
                    {
                        // Grant for engineers
                        "src": ["group:eng"],
                        "dst": ["tag:web"],
                        "ip": ["tcp:443"],
                    },
                ]
            }
            """,
        )
        grants = acl.get_grants()
        assert len(grants) == 1
        assert grants[0]["source_groups"] == ["group:eng"]


# ============================================================================
# transform() tests
# ============================================================================


class TestTransform:
    """Tests for grants transform function."""

    def test_transform_serializes_lists(self) -> None:
        """Transform serializes list/dict fields to JSON strings."""
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
            },
        ]
        result = transform(grants)
        assert result[0]["sources"] == '["group:eng"]'
        assert result[0]["destinations"] == '["tag:web"]'
        assert result[0]["ip_rules"] == '["tcp:443"]'
        assert result[0]["app_capabilities"] is None  # empty dict -> None
        assert result[0]["src_posture"] is None  # empty list -> None

    def test_transform_preserves_relationship_fields(self) -> None:
        """Transform keeps source_groups/users and destination_tags/groups as lists."""
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
            },
        ]
        result = transform(grants)
        assert result[0]["source_users"] == ["alice@ex.com"]
        assert result[0]["destination_tags"] == ["tag:db"]
        assert result[0]["app_capabilities"] == '{"cap": "val"}'
        assert result[0]["src_posture"] == '["posture:x"]'


# ============================================================================
# resolve_access() tests
# ============================================================================


# Test fixtures
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

USERS = [
    {"loginName": "alice@ex.com"},
    {"loginName": "bob@ex.com"},
]


class TestResolveAccessDirectUser:
    """Tests for direct user source resolution."""

    def test_user_to_tag_destination(self) -> None:
        """User source -> tag destination resolves to tagged devices."""
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
            },
        ]
        user_access, group_access, device_access = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
        )
        # tag:web devices: dev-1, dev-4
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        assert user_pairs == {("alice@ex.com", "dev-1"), ("alice@ex.com", "dev-4")}
        assert group_access == []
        assert device_access == []

    def test_user_to_wildcard_destination(self) -> None:
        """User source -> * destination resolves to all devices."""
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
            },
        ]
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        assert user_pairs == {
            ("alice@ex.com", "dev-1"),
            ("alice@ex.com", "dev-2"),
            ("alice@ex.com", "dev-3"),
            ("alice@ex.com", "dev-4"),
        }

    def test_unknown_user_ignored(self) -> None:
        """User not in the users list is ignored."""
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
            },
        ]
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        assert user_access == []

    def test_user_to_autogroup_self(self) -> None:
        """User source -> autogroup:self resolves to user's own devices."""
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
            },
        ]
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        # alice owns dev-1 and dev-2
        assert user_pairs == {("alice@ex.com", "dev-1"), ("alice@ex.com", "dev-2")}


class TestResolveAccessGroup:
    """Tests for group source resolution."""

    def test_group_to_tag_destination(self) -> None:
        """Group source -> tag destination creates group and user access."""
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
            },
        ]
        user_access, group_access, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
        )
        # tag:db devices: dev-3, dev-4
        group_pairs = {(a["group_id"], a["device_id"]) for a in group_access}
        assert group_pairs == {
            ("group:admin", "dev-3"),
            ("group:admin", "dev-4"),
        }
        # group:admin members: alice
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        assert user_pairs == {
            ("alice@ex.com", "dev-3"),
            ("alice@ex.com", "dev-4"),
        }

    def test_group_to_autogroup_self(self) -> None:
        """Group source -> autogroup:self resolves each member to their own devices."""
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
            },
        ]
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        # alice owns dev-1, dev-2; bob owns dev-3, dev-4
        assert user_pairs == {
            ("alice@ex.com", "dev-1"),
            ("alice@ex.com", "dev-2"),
            ("bob@ex.com", "dev-3"),
            ("bob@ex.com", "dev-4"),
        }

    def test_group_destination_resolves_to_member_devices(self) -> None:
        """Group as destination resolves to devices owned by group members."""
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
            },
        ]
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        # group:admin members: alice -> devices dev-1, dev-2
        assert user_pairs == {
            ("alice@ex.com", "dev-1"),
            ("alice@ex.com", "dev-2"),
        }


class TestResolveAccessTagSource:
    """Tests for tag source (device-to-device) resolution."""

    def test_tag_source_to_tag_destination(self) -> None:
        """Tag source -> tag destination creates device-to-device access."""
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
            },
        ]
        _, _, device_access = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        device_pairs = {(a["source_device_id"], a["device_id"]) for a in device_access}
        # tag:web devices: dev-1, dev-4
        # tag:db devices: dev-3, dev-4
        # dev-1 -> dev-3, dev-1 -> dev-4
        # dev-4 -> dev-3 (dev-4 -> dev-4 is self-loop, excluded)
        assert device_pairs == {
            ("dev-1", "dev-3"),
            ("dev-1", "dev-4"),
            ("dev-4", "dev-3"),
        }

    def test_tag_source_to_wildcard(self) -> None:
        """Tag source -> * creates device-to-device access to all (except self)."""
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
            },
        ]
        _, _, device_access = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        device_pairs = {(a["source_device_id"], a["device_id"]) for a in device_access}
        # tag:db devices: dev-3, dev-4
        # Each can access all others (excluding self)
        assert device_pairs == {
            ("dev-3", "dev-1"),
            ("dev-3", "dev-2"),
            ("dev-3", "dev-4"),
            ("dev-4", "dev-1"),
            ("dev-4", "dev-2"),
            ("dev-4", "dev-3"),
        }

    def test_tag_source_no_self_loops(self) -> None:
        """Device-to-device access never creates self-loops."""
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
            },
        ]
        _, _, device_access = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        for entry in device_access:
            assert entry["source_device_id"] != entry["device_id"]


class TestResolveAccessDeduplication:
    """Tests for deduplication logic."""

    def test_user_access_deduplicated(self) -> None:
        """Same user-device pair from multiple grants is deduplicated."""
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
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        # Should be deduplicated: only one entry per (user, device) pair
        user_pairs = [(a["user_login_name"], a["device_id"]) for a in user_access]
        assert len(user_pairs) == len(set(user_pairs))

    def test_user_via_direct_and_group_deduplicated(self) -> None:
        """User appearing both directly and via group membership is deduplicated."""
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
            },
        ]
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        # alice is both a direct source AND a member of group:admin
        # Should only appear once per device
        alice_devices = [
            a["device_id"]
            for a in user_access
            if a["user_login_name"] == "alice@ex.com"
        ]
        assert len(alice_devices) == len(set(alice_devices))


class TestResolveAccessEdgeCases:
    """Tests for edge cases."""

    def test_empty_grants(self) -> None:
        """No grants produces no access."""
        user_access, group_access, device_access = resolve_access(
            [],
            DEVICES,
            GROUPS,
            [],
            USERS,
        )
        assert user_access == []
        assert group_access == []
        assert device_access == []

    def test_grant_with_no_matching_destination(self) -> None:
        """Grant with destination tag that no device has produces no access."""
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
            },
        ]
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        assert user_access == []

    def test_grant_ip_rules_stored_on_relationship(self) -> None:
        """IP rules are serialized and stored on the access relationship."""
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
            },
        ]
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        assert user_access[0]["ip_rules"] == json.dumps(
            ["tcp:443", "tcp:8080"],
            sort_keys=True,
        )
        assert user_access[0]["grant_id"] == "grant:0"

    def test_grant_without_ip_rules(self) -> None:
        """Grant with empty ip_rules stores None."""
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
            },
        ]
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        assert user_access[0]["ip_rules"] is None

    def test_tag_destination_with_port_suffix_stripped(self) -> None:
        """Tag destination like 'tag:web:443' resolves to tag:web devices."""
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
            },
        ]
        user_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        # tag:web devices: dev-1, dev-4
        assert user_pairs == {("alice@ex.com", "dev-1"), ("alice@ex.com", "dev-4")}
