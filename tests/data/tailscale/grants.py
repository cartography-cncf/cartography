TAILSCALE_ACL_FILE_WITH_GRANTS = """
// Example ACL file with grants
{
    // Declare static groups of users.
    "groups": {
        "group:example": ["hjsimpson@simpson.corp"],
        "group:corp":   ["user:*@simpson.corp"],
        "group:employees": ["group:corp", "user:*@ext.simpson.corp"],
    },

    // Define the tags which can be applied to devices and by which users.
    "tagOwners": {
        "tag:byod": ["autogroup:admin"],
        "tag:compromized": ["hjsimpson@simpson.corp"],
    },

    // Define device posture rules
    "postures": {
        "posture:healthySentinelOneMac": [
            "node:os == 'macos'",
            "sentinelOne:infected == false",
        ],
        "posture:healthySentinelOne": [
            "sentinelOne:infected == false",
        ],
    },

    // Define grants (the modern replacement for ACLs)
    "grants": [
        {
            // Grant 0: group:example can access tag:byod devices on tcp:443
            "src": ["group:example"],
            "dst": ["tag:byod"],
            "ip": ["tcp:443"],
        },
        {
            // Grant 1: specific user can access all devices
            "src": ["mbsimpson@simpson.corp"],
            "dst": ["*"],
            "ip": ["*:*"],
        },
        {
            // Grant 2: autogroup:member can access tag:byod with posture check
            "src": ["autogroup:member"],
            "dst": ["tag:byod"],
            "ip": ["tcp:22", "tcp:443"],
            "srcPosture": ["posture:healthySentinelOne"],
        },
        {
            // Grant 3: tag:byod devices can access all devices (device-to-device)
            "src": ["tag:byod"],
            "dst": ["*"],
            "ip": ["tcp:443"],
        },
        {
            // Grant 4: group:employees can access autogroup:self (own devices)
            "src": ["group:employees"],
            "dst": ["autogroup:self"],
            "ip": ["*:*"],
        },
    ],
}"""
