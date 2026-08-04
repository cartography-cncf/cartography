ACCOUNT_WAF_RULESET_ID = "c4e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4"
CUSTOM_FIREWALL_RULESET_ID = "d5f1a2b3c4e5d6f7a8b9c0d1e2f3a4b5"
MANAGED_RULESET_ID = "e6a2b3c4d5f6a7b8c9d0e1f2a3b4c5d6"
CACHE_RULESET_ID = "f7b3c4d5e6a7b8c9d0e1f2a3b4c5d6e7"
OWASP_RULESET_ID = "a8c4d5e6f7b8c9d0e1f2a3b4c5d6e7f8"
BOT_RULESET_ID = "b9d5e6f7a8c9d0e1f2a3b4c5d6e7f8a9"

# The Cloudflare-provided rulesets. They keep the same API ID in every account and
# every zone, and are listed at both levels whether or not anything executes them.
_MANAGED_RULESET = {
    "id": MANAGED_RULESET_ID,
    "name": "Cloudflare Managed Ruleset",
    "kind": "managed",
    "phase": "http_request_firewall_managed",
    "version": "104",
    "description": "Cloudflare-provided managed WAF rules.",
    "last_updated": "2024-06-01T00:00:00.000Z",
}
_OWASP_RULESET = {
    "id": OWASP_RULESET_ID,
    "name": "Cloudflare OWASP Core Ruleset",
    "kind": "managed",
    "phase": "http_request_firewall_managed",
    "version": "42",
    "description": "Cloudflare-provided OWASP core rules.",
    "last_updated": "2024-05-14T00:00:00.000Z",
}
# An account-level custom ruleset. Creating it does not activate it: it only runs
# where an enabled `execute` rule references it, which here is the Simpson zone.
_BOT_RULESET = {
    "id": BOT_RULESET_ID,
    "name": "Springfield bot mitigation",
    "kind": "custom",
    "phase": "http_request_firewall_custom",
    "version": "5",
    "description": "Challenge the scrapers crawling the donut catalogue.",
    "last_updated": "2024-06-22T08:45:00.000Z",
}

# What rulesets.list(account_id=...) returns: the account's phase entry point plus
# everything that may be deployed from it.
CLOUDFLARE_ACCOUNT_RULESETS = [
    {
        "id": ACCOUNT_WAF_RULESET_ID,
        "name": "Springfield account WAF",
        "kind": "root",
        "phase": "http_request_firewall_managed",
        "version": "7",
        "description": "Managed WAF deployed across every Simpson zone.",
        "last_updated": "2024-06-25T14:30:00.000Z",
    },
    _MANAGED_RULESET,
    _OWASP_RULESET,
    _BOT_RULESET,
]

# What rulesets.list(zone_id=...) returns: the zone's own phase entry points, plus
# the account-level rulesets one may want to deploy to this zone and the
# Cloudflare-provided ones. Only some of them are actually deployed here.
CLOUDFLARE_ZONE_RULESETS = [
    {
        "id": CUSTOM_FIREWALL_RULESET_ID,
        "name": "Simpson custom firewall",
        "kind": "zone",
        "phase": "http_request_firewall_custom",
        "version": "12",
        "description": "Block traffic Bart should not be sending.",
        "last_updated": "2024-06-20T10:15:00.000Z",
    },
    {
        "id": CACHE_RULESET_ID,
        "name": "Simpson cache settings",
        "kind": "zone",
        "phase": "http_request_cache_settings",
        "version": "3",
        "description": "Cache the donut catalogue aggressively.",
        "last_updated": "2024-02-14T09:00:00.000Z",
    },
    _MANAGED_RULESET,
    _OWASP_RULESET,
    _BOT_RULESET,
    # The account's entry point ruleset also shows up in the zone listing. It is
    # deployed at the account level, not in this zone.
    {
        "id": ACCOUNT_WAF_RULESET_ID,
        "name": "Springfield account WAF",
        "kind": "root",
        "phase": "http_request_firewall_managed",
        "version": "7",
        "description": "Managed WAF deployed across every Simpson zone.",
        "last_updated": "2024-06-25T14:30:00.000Z",
    },
]

ACCOUNT_EXECUTE_RULE_ID = "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e701"
BLOCK_RULE_ID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c501"
CHALLENGE_RULE_ID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c502"
ZONE_EXECUTE_RULE_ID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c503"
ZONE_EXECUTE_BOT_RULE_ID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c504"
ZONE_DISABLED_EXECUTE_RULE_ID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c505"
CACHE_RULE_ID = "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d601"
BOT_RULE_ID = "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f801"

# Keyed by ruleset ID, as returned by rulesets.get().rules. The Cloudflare-provided
# rulesets are absent on purpose: their contents are vendor-owned and never
# fetched.
CLOUDFLARE_RULESET_RULES = {
    ACCOUNT_WAF_RULESET_ID: [
        {
            "id": ACCOUNT_EXECUTE_RULE_ID,
            "version": "7",
            "action": "execute",
            "expression": "true",
            "description": "Deploy the managed WAF to every zone in the account.",
            "enabled": True,
            "ref": ACCOUNT_EXECUTE_RULE_ID,
            "last_updated": "2024-06-25T14:30:00.000Z",
            "action_parameters": {"id": MANAGED_RULESET_ID},
        },
    ],
    CUSTOM_FIREWALL_RULESET_ID: [
        {
            "id": BLOCK_RULE_ID,
            "version": "12",
            "action": "block",
            "expression": '(http.request.uri.path contains "/skateboard")',
            "description": "Block skateboard purchases.",
            "enabled": True,
            "ref": BLOCK_RULE_ID,
            "last_updated": "2024-06-20T10:15:00.000Z",
            "categories": [],
            "logging": {"enabled": True},
        },
        {
            "id": CHALLENGE_RULE_ID,
            "version": "12",
            "action": "managed_challenge",
            "expression": '(http.request.uri.path eq "/login")',
            "description": "Challenge repeated login attempts.",
            "enabled": True,
            "ref": CHALLENGE_RULE_ID,
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
            "id": ZONE_EXECUTE_RULE_ID,
            "version": "12",
            "action": "execute",
            "expression": "true",
            "description": "Turn on the Cloudflare Managed Ruleset.",
            "enabled": True,
            "ref": ZONE_EXECUTE_RULE_ID,
            "last_updated": "2024-06-20T10:15:00.000Z",
            "action_parameters": {"id": MANAGED_RULESET_ID},
        },
        {
            "id": ZONE_EXECUTE_BOT_RULE_ID,
            "version": "12",
            "action": "execute",
            "expression": "true",
            "description": "Run the account's bot mitigation ruleset here.",
            "enabled": True,
            "ref": ZONE_EXECUTE_BOT_RULE_ID,
            "last_updated": "2024-06-22T08:45:00.000Z",
            "action_parameters": {"id": BOT_RULESET_ID},
        },
        # Turned off, so the OWASP core ruleset does not run in this zone.
        {
            "id": ZONE_DISABLED_EXECUTE_RULE_ID,
            "version": "12",
            "action": "execute",
            "expression": "true",
            "description": "OWASP core rules, turned off after too many false positives.",
            "enabled": False,
            "ref": ZONE_DISABLED_EXECUTE_RULE_ID,
            "last_updated": "2024-06-18T16:00:00.000Z",
            "action_parameters": {"id": OWASP_RULESET_ID},
        },
    ],
    CACHE_RULESET_ID: [
        {
            "id": CACHE_RULE_ID,
            "version": "3",
            "action": "set_cache_settings",
            "expression": '(http.request.uri.path contains "/catalogue")',
            "description": "Cache the catalogue.",
            "enabled": True,
            "ref": CACHE_RULE_ID,
            "last_updated": "2024-02-14T09:00:00.000Z",
        },
    ],
    BOT_RULESET_ID: [
        {
            "id": BOT_RULE_ID,
            "version": "5",
            "action": "js_challenge",
            "expression": "(cf.client.bot)",
            "description": "Challenge known bots.",
            "enabled": True,
            "ref": BOT_RULE_ID,
            "last_updated": "2024-06-22T08:45:00.000Z",
            "categories": [],
            "logging": {"enabled": True},
        },
    ],
}
