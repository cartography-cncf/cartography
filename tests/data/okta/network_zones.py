from typing import Any

# Synthetic raw API payloads for GET /api/v1/zones.

TS = "2026-01-01T00:00:00.000Z"

NETWORK_ZONES: list[dict[str, Any]] = [
    {
        "id": "nzo-corp",
        "type": "IP",
        "name": "Corporate egress",
        "status": "ACTIVE",
        "usage": "POLICY",
        "system": False,
        "created": TS,
        "lastUpdated": TS,
        "gateways": [
            {"type": "CIDR", "value": "198.51.100.0/24"},
            {"type": "RANGE", "value": "203.0.113.10-203.0.113.20"},
        ],
        "proxies": [{"type": "CIDR", "value": "192.0.2.10/32"}],
        "useAsExemptList": False,
    },
    {
        "id": "nzo-blocked-ips",
        "type": "IP",
        "name": "BlockedIpZone",
        "status": "ACTIVE",
        "usage": "BLOCKLIST",
        "system": True,
        "created": TS,
        "lastUpdated": TS,
        "gateways": [{"type": "CIDR", "value": "233.252.0.0/24"}],
        "proxies": None,
    },
    {
        "id": "nzo-tor",
        "type": "DYNAMIC",
        "name": "Tor and embargoed countries",
        "status": "ACTIVE",
        "usage": "BLOCKLIST",
        "system": False,
        "created": TS,
        "lastUpdated": TS,
        "proxyType": "TorAnonymizer",
        "asns": [64496, "64497"],
        "locations": [
            {"country": "AQ", "region": None},
            {"country": "US", "region": "US-AK"},
        ],
    },
    {
        "id": "nzo-enhanced-dynamic",
        "type": "DYNAMIC_V2",
        "name": "DefaultEnhancedDynamicZone",
        "status": "ACTIVE",
        "usage": "BLOCKLIST",
        "system": True,
        "created": TS,
        "lastUpdated": TS,
        "asns": {"include": [], "exclude": ["64498"]},
        "locations": {"include": [], "exclude": [{"country": "CA"}]},
        # A category newer than the SDK enum must not break the sync.
        "ipServiceCategories": {
            "include": ["ALL_ANONYMIZERS", "FUTURE_CATEGORY"],
            "exclude": [],
        },
    },
]
