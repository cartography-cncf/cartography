ADMIN_ROLE_ID = "a1b2c3d4-0000-4000-8000-000000000001"
MEMBER_ROLE_ID = "a1b2c3d4-0000-4000-8000-000000000002"
SECURITY_ROLE_ID = "a1b2c3d4-0000-4000-8000-000000000003"

PYLON_ROLES = [
    {
        "id": ADMIN_ROLE_ID,
        "name": "Admin",
        "slug": "admin",
        "permissions": [
            {"action": "read:issue"},
            {"action": "write:issue"},
            {"action": "delete:issue"},
            {"action": "manage:users"},
        ],
        "issue_access_policy": {
            "default_actions": ["read", "write", "delete"],
            "rules": [],
        },
    },
    {
        "id": MEMBER_ROLE_ID,
        "name": "Member",
        "slug": "member",
        "permissions": [
            {"action": "read:issue"},
            {"action": "write:issue"},
        ],
        "issue_access_policy": {
            "default_actions": ["read", "write"],
            "rules": [],
        },
    },
    {
        "id": SECURITY_ROLE_ID,
        "name": "Security",
        "slug": "security",
        "permissions": [
            {
                "action": "read:account",
                "filter": {
                    "field": "owner_id",
                    "operator": "equals",
                    "value": "current_user",
                },
            },
            {"action": "read:issue", "filter_unsupported": True},
            {"action": "write:contact", "field_restrictions_unsupported": True},
        ],
        "issue_access_policy": {
            "default_actions": [],
            "rules": [
                {
                    "id": "rule-1",
                    "actions": ["read", "write"],
                    "filter": {
                        "field": "workspace_email",
                        "operator": "equals",
                        "value": "security@simpson.corp",
                    },
                },
            ],
        },
    },
]
