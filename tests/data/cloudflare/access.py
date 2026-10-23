# Synthetic provider responses; no real account or identity data.
APPLICATIONS = [
    {
        "id": "app-one",
        "name": "Internal dashboard",
        "type": "self_hosted",
        "domain": "dashboard.example.com/admin",
        "session_duration": "24h",
        "aud": "aud-one",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
    },
    {"id": "app-two", "name": "Bookmark", "type": "bookmark", "domain": None},
]
POLICIES = [
    {
        "id": "shared-policy",
        "name": "Engineering",
        "decision": "allow",
        "precedence": 1,
        "session_duration": "8h",
        "include": [{"email_domain": {"domain": "example.com"}}],
        "require": [{"group": {"id": "synthetic-group"}}],
        "exclude": [{"email": {"email": "excluded@example.com"}}],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
    },
    {
        "id": "bypass-policy",
        "name": "Public endpoint",
        "decision": "bypass",
        "precedence": 2,
        "include": [{"everyone": {}}],
        "require": [],
        "exclude": None,
    },
]

DNS_ZONES = [
    {"id": "zone", "name": "example.com"},
    {"id": "child-zone", "name": "child.example.com"},
    {"id": "net-zone", "name": "example.net"},
]
DNS_RECORDS = [
    {
        "id": "dashboard",
        "name": "dashboard.example.com",
        "type": "A",
        "proxied": True,
        "zone_id": "zone",
    },
    {
        "id": "ipv6",
        "name": "ipv6.example.com",
        "type": "AAAA",
        "proxied": True,
        "zone_id": "zone",
    },
    {
        "id": "alias",
        "name": "alias.example.com",
        "type": "CNAME",
        "proxied": True,
        "zone_id": "zone",
    },
    {
        "id": "apex",
        "name": "example.com",
        "type": "A",
        "proxied": True,
        "zone_id": "zone",
    },
    {
        "id": "deep",
        "name": "two.deep.example.com",
        "type": "A",
        "proxied": True,
        "zone_id": "zone",
    },
    {
        "id": "dns-only",
        "name": "dns-only.example.com",
        "type": "A",
        "proxied": False,
        "zone_id": "zone",
    },
    {
        "id": "txt",
        "name": "txt.example.com",
        "type": "TXT",
        "proxied": False,
        "zone_id": "zone",
    },
    {
        "id": "wildcard",
        "name": "*.example.com",
        "type": "A",
        "proxied": True,
        "zone_id": "zone",
    },
    {
        "id": "child",
        "name": "a.child.example.com",
        "type": "A",
        "proxied": True,
        "zone_id": "child-zone",
    },
    {
        "id": "net",
        "name": "a.example.net",
        "type": "A",
        "proxied": True,
        "zone_id": "net-zone",
    },
]
