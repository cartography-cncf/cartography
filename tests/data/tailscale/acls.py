TAILSCALE_ACL_FILE = """
// Example/default ACLs for unrestricted connections.
{
    // Declare static groups of users. Use autogroups for all users or users with a specific role.
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

    // Define access control lists for users, groups, autogroups, tags,
    // Tailscale IP addresses, and subnet ranges.
    "acls": [
        // Allow all connections.
        // Comment this section out if you want to define specific restrictions.
        {"action": "accept", "src": ["*"], "dst": ["*:*"]},

        // Allow users in "group:example" to access "tag:example", but only from
        // devices that are running macOS and have enabled Tailscale client auto-updating.
        // {"action": "accept", "src": ["group:example"], "dst": ["tag:example:*"], "srcPosture":["posture:autoUpdateMac"]},
    ],

    // Define postures that will be applied to all rules without any specific
    // srcPosture definition.
    // "defaultSrcPosture": [
    //      "posture:anyMac",
    // ],

    // Define device posture rules requiring devices to meet
    // certain criteria to access parts of your system.
    // "postures": {
    //      // Require devices running macOS, a stable Tailscale
    //      // version and auto update enabled for Tailscale.
    //     "posture:autoUpdateMac": [
    //         "node:os == 'macos'",
    //         "node:tsReleaseTrack == 'stable'",
    //         "node:tsAutoUpdate",
    //     ],
    //      // Require devices running macOS and a stable
    //      // Tailscale version.
    //     "posture:anyMac": [
    //         "node:os == 'macos'",
    //         "node:tsReleaseTrack == 'stable'",
    //     ],
    // },

    // Define users and devices that can use Tailscale SSH.
    "ssh": [
        // Allow all users to SSH into their own devices in check mode.
        // Comment this section out if you want to define specific restrictions.
        {
            "action": "check",
            "src":    ["autogroup:member"],
            "dst":    ["autogroup:self"],
            "users":  ["autogroup:nonroot", "root"],
        },
    ],

    // Test access rules every time they're saved.
    // "tests": [
    //      {
    //          "src": "alice@example.com",
    //          "accept": ["tag:example"],
    //          "deny": ["100.101.102.103:443"],
    //      },
    // ],
}"""
