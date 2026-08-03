CLOUDFLARE_ACCOUNT_RULESETS = [
    {
        "id": "c4e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4",
        "name": "Springfield account WAF",
        "kind": "root",
        "phase": "http_request_firewall_managed",
        "version": "7",
        "description": "Managed WAF deployed across every Simpson zone.",
        "last_updated": "2024-06-25T14:30:00.000Z",
    },
    # The same Cloudflare-provided ruleset is listed at the account level and in
    # every zone, always under this one API ID.
    {
        "id": "e6a2b3c4d5f6a7b8c9d0e1f2a3b4c5d6",
        "name": "Cloudflare Managed Ruleset",
        "kind": "managed",
        "phase": "http_request_firewall_managed",
        "version": "104",
        "description": "Cloudflare-provided managed WAF rules.",
        "last_updated": "2024-06-01T00:00:00.000Z",
    },
]

CLOUDFLARE_ZONE_RULESETS = [
    {
        "id": "d5f1a2b3c4e5d6f7a8b9c0d1e2f3a4b5",
        "name": "Simpson custom firewall",
        "kind": "zone",
        "phase": "http_request_firewall_custom",
        "version": "12",
        "description": "Block traffic Bart should not be sending.",
        "last_updated": "2024-06-20T10:15:00.000Z",
    },
    {
        "id": "e6a2b3c4d5f6a7b8c9d0e1f2a3b4c5d6",
        "name": "Cloudflare Managed Ruleset",
        "kind": "managed",
        "phase": "http_request_firewall_managed",
        "version": "104",
        "description": "Cloudflare-provided managed WAF rules.",
        "last_updated": "2024-06-01T00:00:00.000Z",
    },
    {
        "id": "f7b3c4d5e6a7b8c9d0e1f2a3b4c5d6e7",
        "name": "Simpson cache settings",
        "kind": "zone",
        "phase": "http_request_cache_settings",
        "version": "3",
        "description": "Cache the donut catalogue aggressively.",
        "last_updated": "2024-02-14T09:00:00.000Z",
    },
]

# Keyed by ruleset ID, as returned by rulesets.get().rules. The managed ruleset
# is absent on purpose: its contents are vendor-owned and never fetched.
CLOUDFLARE_RULESET_RULES = {
    "c4e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4": [
        {
            "id": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e701",
            "version": "7",
            "action": "execute",
            "expression": "true",
            "description": "Deploy the managed WAF to every zone in the account.",
            "enabled": True,
            "ref": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e701",
            "last_updated": "2024-06-25T14:30:00.000Z",
            "action_parameters": {"id": "e6a2b3c4d5f6a7b8c9d0e1f2a3b4c5d6"},
        },
    ],
    "d5f1a2b3c4e5d6f7a8b9c0d1e2f3a4b5": [
        {
            "id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c501",
            "version": "12",
            "action": "block",
            "expression": '(http.request.uri.path contains "/skateboard")',
            "description": "Block skateboard purchases.",
            "enabled": True,
            "ref": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c501",
            "last_updated": "2024-06-20T10:15:00.000Z",
            "categories": [],
            "logging": {"enabled": True},
        },
        {
            "id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c502",
            "version": "12",
            "action": "managed_challenge",
            "expression": '(http.request.uri.path eq "/login")',
            "description": "Challenge repeated login attempts.",
            "enabled": True,
            "ref": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c502",
            "last_updated": "2024-06-20T10:15:00.000Z",
            "categories": [],
            "logging": {"enabled": True},
            "ratelimit": {
                "characteristics": ["ip.src"],
                "period": 60,
                "requests_per_period": 10,
            },
        },
        {
            "id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c503",
            "version": "12",
            "action": "execute",
            "expression": "true",
            "description": "Turn on the Cloudflare Managed Ruleset.",
            "enabled": True,
            "ref": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c503",
            "last_updated": "2024-06-20T10:15:00.000Z",
            "action_parameters": {"id": "e6a2b3c4d5f6a7b8c9d0e1f2a3b4c5d6"},
        },
    ],
    "f7b3c4d5e6a7b8c9d0e1f2a3b4c5d6e7": [
        {
            "id": "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d601",
            "version": "3",
            "action": "set_cache_settings",
            "expression": '(http.request.uri.path contains "/catalogue")',
            "description": "Cache the catalogue.",
            "enabled": True,
            "ref": "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d601",
            "last_updated": "2024-02-14T09:00:00.000Z",
        },
    ],
}
