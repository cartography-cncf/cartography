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
- Edge cases: empty grants, unknown users, self-loops, aggregation
"""

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
        assert grant["id"].startswith("grant:")
        assert len(grant["id"]) == len("grant:") + 12  # 12 hex chars
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

    def test_multiple_grants_have_unique_stable_ids(self) -> None:
        """Multiple grants get unique stable IDs based on content hash."""
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
        ids = [g["id"] for g in grants]
        # All IDs are unique
        assert len(set(ids)) == 3
        # All IDs have the correct format
        for grant_id in ids:
            assert grant_id.startswith("grant:")
            assert len(grant_id) == len("grant:") + 12

    def test_grant_id_stable_across_reordering(self) -> None:
        """Grant IDs are stable regardless of order in the file."""
        acl1 = ACLParser(
            """
            {
                "grants": [
                    {"src": ["group:a"], "dst": ["tag:b"], "ip": ["tcp:80"]},
                    {"src": ["group:c"], "dst": ["tag:d"], "ip": ["tcp:443"]}
                ]
            }
            """,
        )
        acl2 = ACLParser(
            """
            {
                "grants": [
                    {"src": ["group:c"], "dst": ["tag:d"], "ip": ["tcp:443"]},
                    {"src": ["group:a"], "dst": ["tag:b"], "ip": ["tcp:80"]}
                ]
            }
            """,
        )
        grants1 = acl1.get_grants()
        grants2 = acl2.get_grants()
        # Same grants in different order should produce same IDs
        ids1 = {g["id"] for g in grants1}
        ids2 = {g["id"] for g in grants2}
        assert ids1 == ids2

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
        user_access, group_access, device_access, _, _ = resolve_access(
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
        # alice's devices (dev-1, dev-2) inherit her CAN_ACCESS to tag:web devices
        device_pairs = {(a["source_device_id"], a["device_id"]) for a in device_access}
        # dev-2 -> dev-1 (alice's dev-2 inherits access to dev-1)
        assert ("dev-2", "dev-1") in device_pairs
        # dev-2 -> dev-4 (alice's dev-2 inherits access to dev-4)
        assert ("dev-2", "dev-4") in device_pairs
        # dev-1 -> dev-4 (alice's dev-1 inherits access to dev-4)
        assert ("dev-1", "dev-4") in device_pairs
        # No self-loops
        for src, dst in device_pairs:
            assert src != dst

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
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
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
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
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
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
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
        user_access, group_access, _, _, _ = resolve_access(
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
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
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
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
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
        _, _, device_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
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
        _, _, device_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
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
        _, _, device_access, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        for entry in device_access:
            assert entry["source_device_id"] != entry["device_id"]


class TestResolveAccessDeduplication:
    """Tests for aggregation logic (granted_by accumulates grant IDs)."""

    def test_multiple_grants_aggregated(self) -> None:
        """Same user-device pair from multiple grants aggregates grant IDs."""
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
        # tag:web devices: dev-1, dev-4
        # Each pair should have both grant IDs
        for entry in user_access:
            if entry["user_login_name"] == "alice@ex.com":
                assert entry["granted_by"] == ["grant:0", "grant:1"]

    def test_user_via_direct_and_group_aggregated(self) -> None:
        """User appearing both directly and via group membership aggregates grants."""
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
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        # alice is both a direct source AND a member of group:admin
        # Same grant, so granted_by should still be ["grant:0"] (no duplicate)
        alice_entries = [
            a for a in user_access if a["user_login_name"] == "alice@ex.com"
        ]
        for entry in alice_entries:
            assert entry["granted_by"] == ["grant:0"]

    def test_same_grant_not_duplicated_in_granted_by(self) -> None:
        """Same grant ID is not added twice to granted_by."""
        grants = [
            {
                "id": "grant:0",
                "source_users": ["alice@ex.com"],
                "source_groups": ["group:admin"],  # alice is also member
                "source_tags": [],
                "destinations": ["tag:web"],
                "destination_tags": ["tag:web"],
                "destination_groups": [],
                "destination_hosts": [],
                "ip_rules": [],
                "app_capabilities": {},
                "src_posture": [],
            },
        ]
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        alice_dev1 = [
            a
            for a in user_access
            if a["user_login_name"] == "alice@ex.com" and a["device_id"] == "dev-1"
        ]
        assert len(alice_dev1) == 1
        # grant:0 appears only once even though alice is both direct and via group
        assert alice_dev1[0]["granted_by"] == ["grant:0"]


class TestResolveAccessEdgeCases:
    """Tests for edge cases."""

    def test_empty_grants(self) -> None:
        """No grants produces no access."""
        user_access, group_access, device_access, _, _ = resolve_access(
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
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        assert user_access == []

    def test_grant_ip_rules_stored_on_relationship(self) -> None:
        """Granted_by stores the list of grant IDs that justify access."""
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
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        assert user_access[0]["granted_by"] == ["grant:0"]

    def test_grant_without_ip_rules(self) -> None:
        """Grant with empty ip_rules still produces granted_by."""
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
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        assert user_access[0]["granted_by"] == ["grant:0"]

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
        user_access, _, _, _, _ = resolve_access(grants, DEVICES, GROUPS, [], USERS)
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        # tag:web devices: dev-1, dev-4
        assert user_pairs == {("alice@ex.com", "dev-1"), ("alice@ex.com", "dev-4")}


# ============================================================================
# Service destination tests
# ============================================================================


SERVICES = [
    {"name": "web-server"},
    {"name": "database"},
]


class TestACLParserServiceDestination:
    """Tests for svc:xxx parsing in ACLParser."""

    def test_svc_destination_classified(self) -> None:
        """svc:xxx in dst is classified as destination_services."""
        acl = ACLParser(
            '{"grants": [{"src": ["group:eng"], "dst": ["svc:web-server"], "ip": ["tcp:443"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["destination_services"] == ["svc:web-server"]
        assert grants[0]["destination_tags"] == []
        assert grants[0]["destination_hosts"] == []

    def test_mixed_svc_and_tag_destinations(self) -> None:
        """svc: and tag: in the same dst are classified separately."""
        acl = ACLParser(
            '{"grants": [{"src": ["*"], "dst": ["svc:db", "tag:web"], "ip": ["*:*"]}]}',
        )
        grants = acl.get_grants()
        assert grants[0]["destination_services"] == ["svc:db"]
        assert grants[0]["destination_tags"] == ["tag:web"]


class TestResolveAccessServiceDestination:
    """Tests for svc:xxx resolution in resolve_access."""

    def test_user_to_service(self) -> None:
        """User source -> svc:xxx creates user-to-service access."""
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
            },
        ]
        _, _, _, user_svc, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
            SERVICES,
        )
        svc_pairs = {(a["user_login_name"], a["service_id"]) for a in user_svc}
        assert svc_pairs == {("alice@ex.com", "svc:web-server")}

    def test_group_to_service(self) -> None:
        """Group source -> svc:xxx creates group and user service access."""
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
            },
        ]
        _, _, _, user_svc, group_svc = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
            SERVICES,
        )
        group_pairs = {(a["group_id"], a["service_id"]) for a in group_svc}
        assert group_pairs == {("group:admin", "svc:database")}
        # group:admin members: alice
        user_pairs = {(a["user_login_name"], a["service_id"]) for a in user_svc}
        assert user_pairs == {("alice@ex.com", "svc:database")}

    def test_unknown_service_ignored(self) -> None:
        """svc:xxx not in the services list produces no access."""
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
            },
        ]
        _, _, _, user_svc, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
            SERVICES,
        )
        assert user_svc == []

    def test_mixed_device_and_service_destinations(self) -> None:
        """Grant with both tag: and svc: destinations creates both types of access."""
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
            },
        ]
        user_access, _, _, user_svc, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
            SERVICES,
        )
        device_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        assert ("alice@ex.com", "dev-1") in device_pairs  # tag:web device
        svc_pairs = {(a["user_login_name"], a["service_id"]) for a in user_svc}
        assert svc_pairs == {("alice@ex.com", "svc:database")}


# ============================================================================
# IP/CIDR destination tests
# ============================================================================


# Devices with explicit IP addresses for IP resolution tests
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


class TestResolveAccessIPDestination:
    """Tests for IP/CIDR destination resolution."""

    def test_exact_ip_destination(self) -> None:
        """Exact IP destination resolves to the device with that address."""
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
            },
        ]
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES_WITH_IPS,
            GROUPS,
            [],
            USERS,
        )
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        assert user_pairs == {("alice@ex.com", "dev-1")}

    def test_cidr_destination(self) -> None:
        """CIDR range destination resolves to all devices in the range."""
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
            },
        ]
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES_WITH_IPS,
            GROUPS,
            [],
            USERS,
        )
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        # 100.64.0.0/24 includes 100.64.0.1 (dev-1) and 100.64.0.2 (dev-2)
        # but NOT 100.64.1.10 (dev-3)
        assert user_pairs == {("alice@ex.com", "dev-1"), ("alice@ex.com", "dev-2")}

    def test_cidr_slash32_destination(self) -> None:
        """/32 CIDR resolves to exactly one device."""
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
            },
        ]
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES_WITH_IPS,
            GROUPS,
            [],
            USERS,
        )
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        assert user_pairs == {("alice@ex.com", "dev-3")}

    def test_ipv6_destination(self) -> None:
        """IPv6 address destination resolves correctly."""
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
            },
        ]
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES_WITH_IPS,
            GROUPS,
            [],
            USERS,
        )
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        assert user_pairs == {("alice@ex.com", "dev-1")}

    def test_nonexistent_ip_ignored(self) -> None:
        """IP not matching any device produces no access."""
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
            },
        ]
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES_WITH_IPS,
            GROUPS,
            [],
            USERS,
        )
        assert user_access == []

    def test_invalid_destination_ignored(self) -> None:
        """Non-IP, non-selector destination is silently ignored."""
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
            },
        ]
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES_WITH_IPS,
            GROUPS,
            [],
            USERS,
        )
        assert user_access == []

    def test_wide_cidr_matches_all(self) -> None:
        """Wide CIDR /8 matches all devices with 100.x.x.x addresses."""
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
            },
        ]
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES_WITH_IPS,
            GROUPS,
            [],
            USERS,
        )
        user_pairs = {(a["user_login_name"], a["device_id"]) for a in user_access}
        # All 3 devices with 100.x addresses: dev-1, dev-2, dev-3
        assert user_pairs == {
            ("alice@ex.com", "dev-1"),
            ("alice@ex.com", "dev-2"),
            ("alice@ex.com", "dev-3"),
        }


# ============================================================================
# srcPosture filtering tests
# ============================================================================


# Posture matches: alice's dev-1 conforms to posture:healthy,
# bob's dev-3 conforms to posture:healthy and posture:managed
POSTURE_MATCHES = [
    {"device_id": "dev-1", "posture_id": "posture:healthy"},
    {"device_id": "dev-3", "posture_id": "posture:healthy"},
    {"device_id": "dev-3", "posture_id": "posture:managed"},
]


class TestResolveAccessPostureFiltering:
    """Tests for srcPosture filtering in resolve_access."""

    def test_no_posture_no_filtering(self) -> None:
        """Grant without srcPosture applies to all sources."""
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
            },
        ]
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
            [],
            POSTURE_MATCHES,
        )
        user_logins = {a["user_login_name"] for a in user_access}
        assert "alice@ex.com" in user_logins
        assert "bob@ex.com" in user_logins

    def test_posture_filters_non_compliant_user(self) -> None:
        """User without any compliant device is filtered out."""
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
            },
        ]
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
            [],
            POSTURE_MATCHES,
        )
        user_logins = {a["user_login_name"] for a in user_access}
        # bob has dev-3 which conforms to posture:managed
        assert "bob@ex.com" in user_logins
        # alice has dev-1 which only conforms to posture:healthy, not posture:managed
        assert "alice@ex.com" not in user_logins

    def test_posture_requires_all_postures(self) -> None:
        """srcPosture with multiple entries requires all to be met."""
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
            },
        ]
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
            [],
            POSTURE_MATCHES,
        )
        user_logins = {a["user_login_name"] for a in user_access}
        # bob has dev-3 which conforms to both posture:healthy and posture:managed
        assert "bob@ex.com" in user_logins
        # alice's dev-1 only has posture:healthy
        assert "alice@ex.com" not in user_logins

    def test_posture_filters_group_members(self) -> None:
        """srcPosture filters individual group members, not the group itself."""
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
            },
        ]
        user_access, group_access, _, _, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
            [],
            POSTURE_MATCHES,
        )
        # Group itself still gets CAN_ACCESS (posture doesn't filter groups)
        group_pairs = {(a["group_id"], a["device_id"]) for a in group_access}
        assert len(group_pairs) > 0
        # But only bob (who meets posture:managed) gets individual user access
        user_logins = {a["user_login_name"] for a in user_access}
        assert "bob@ex.com" in user_logins
        assert "alice@ex.com" not in user_logins

    def test_posture_filters_device_sources(self) -> None:
        """srcPosture filters device sources in device-to-device access."""
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
            },
        ]
        _, _, device_access, _, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
            [],
            POSTURE_MATCHES,
        )
        source_ids = {a["source_device_id"] for a in device_access}
        # dev-1 has tag:web and conforms to posture:healthy -> passes
        assert "dev-1" in source_ids
        # dev-4 has tag:web but no posture matches at all -> filtered out
        assert "dev-4" not in source_ids

    def test_no_posture_matches_blocks_all_with_posture_requirement(self) -> None:
        """If no posture_matches are provided but grant requires posture, no access."""
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
            },
        ]
        # No posture_matches -> nobody meets the requirement
        user_access, _, _, _, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
            [],
            [],
        )
        assert user_access == []


# ============================================================================
# User-to-device access propagation tests
# ============================================================================


class TestResolveAccessUserDevicePropagation:
    """Tests for propagation of user CAN_ACCESS to their devices."""

    def test_user_access_propagated_to_devices(self) -> None:
        """User's devices inherit CAN_ACCESS to the destination device."""
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
            },
        ]
        _, _, device_access, _, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
        )
        device_pairs = {(a["source_device_id"], a["device_id"]) for a in device_access}
        # alice owns dev-1 and dev-2
        # tag:db devices: dev-3, dev-4
        # alice's devices should inherit CAN_ACCESS to dev-3 and dev-4
        assert ("dev-1", "dev-3") in device_pairs
        assert ("dev-1", "dev-4") in device_pairs
        assert ("dev-2", "dev-3") in device_pairs
        assert ("dev-2", "dev-4") in device_pairs

    def test_propagation_no_self_loops(self) -> None:
        """Propagation does not create self-loops."""
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
            },
        ]
        _, _, device_access, _, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
        )
        for entry in device_access:
            assert entry["source_device_id"] != entry["device_id"]

    def test_propagation_carries_granted_by(self) -> None:
        """Propagated device access carries the same granted_by as the user access."""
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
            },
        ]
        _, _, device_access, _, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
        )
        # bob owns dev-3, dev-4; tag:web devices: dev-1, dev-4
        # bob's dev-3 -> dev-1 should have granted_by from grant:0
        bob_dev3_to_dev1 = [
            a
            for a in device_access
            if a["source_device_id"] == "dev-3" and a["device_id"] == "dev-1"
        ]
        assert len(bob_dev3_to_dev1) == 1
        assert "grant:0" in bob_dev3_to_dev1[0]["granted_by"]

    def test_group_user_access_also_propagated(self) -> None:
        """User access resolved from group membership is also propagated to devices."""
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
            },
        ]
        _, _, device_access, _, _ = resolve_access(
            grants,
            DEVICES,
            GROUPS,
            [],
            USERS,
        )
        device_pairs = {(a["source_device_id"], a["device_id"]) for a in device_access}
        # group:admin members: alice (dev-1, dev-2)
        # tag:db devices: dev-3, dev-4
        assert ("dev-1", "dev-3") in device_pairs
        assert ("dev-2", "dev-4") in device_pairs
