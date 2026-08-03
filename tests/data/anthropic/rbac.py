ANTHROPIC_RBAC_ROLES = [
    {
        "id": "rbac_role_016J8xVtKpDq3Wy9ZmN2hR4s",
        "type": "rbac_role",
        "name": "Project Editor",
        "created_at": "2025-04-01T09:00:00.000000Z",
        "updated_at": "2025-04-01T09:00:00.000000Z",
    },
    {
        "id": "rbac_role_02Tf7NqWrBz5Xk1LcPd8Ju6M",
        "type": "rbac_role",
        "name": "Plant Supervisor",
        "created_at": "2025-04-02T09:00:00.000000Z",
        "updated_at": "2025-04-02T09:00:00.000000Z",
    },
]

# Keyed by role id, as returned by
# GET /organizations/rbac_roles/{id}/permissions
ANTHROPIC_RBAC_ROLE_PERMISSIONS = {
    "rbac_role_016J8xVtKpDq3Wy9ZmN2hR4s": [
        {
            "type": "rbac_role_permission",
            "action": "chat",
            "resource": {
                "type": "organization",
                "organization_id": "8834c225-ea27-405a-aea9-5ed5f07f4858",
            },
        },
        {
            "type": "rbac_role_permission",
            "action": "use",
            "resource": {
                "type": "connector_tool",
                "connector_id": "conn_01ReactorTelemetry",
                "tool_name": "read_sensor",
            },
        },
    ],
    # capability_access_all is a blanket grant: it stands for every product-feature
    # entitlement, so it must not be read as a single narrow permission.
    "rbac_role_02Tf7NqWrBz5Xk1LcPd8Ju6M": [
        {
            "type": "rbac_role_permission",
            "action": "capability_access_all",
            "resource": {
                "type": "organization",
                "organization_id": "8834c225-ea27-405a-aea9-5ed5f07f4858",
            },
        },
    ],
}

ANTHROPIC_RBAC_GROUPS = [
    {
        "id": "rbac_group_012rppKaSVsmTo6NqRDXQXNF",
        "type": "rbac_group",
        "name": "Engineering",
        "source_type": "direct",
        "roles": ["rbac_role_016J8xVtKpDq3Wy9ZmN2hR4s"],
        "created_at": "2025-04-03T09:00:00.000000Z",
        "updated_at": "2025-04-03T09:00:00.000000Z",
    },
    # A null roles field means the role data was temporarily unavailable, not that
    # the group holds no roles.
    {
        "id": "rbac_group_03Yh4MjXsQe7Rv2BnKt9Wz5D",
        "type": "rbac_group",
        "name": "Safety Inspectors",
        "source_type": "scim",
        "roles": None,
        "created_at": "2025-04-04T09:00:00.000000Z",
        "updated_at": "2025-04-04T09:00:00.000000Z",
    },
]

# Keyed by group id, as returned by
# GET /organizations/rbac_groups/{id}/members
ANTHROPIC_RBAC_GROUP_MEMBERS = {
    "rbac_group_012rppKaSVsmTo6NqRDXQXNF": [
        {
            "type": "rbac_group_member",
            "group_id": "rbac_group_012rppKaSVsmTo6NqRDXQXNF",
            "user_id": "user_EneequohSheesh3Ohtaefu8we2aite",
            "email": "hjsimpson@simpson.corp",
            "created_at": "2025-04-03T09:00:00.000000Z",
        },
    ],
    "rbac_group_03Yh4MjXsQe7Rv2BnKt9Wz5D": [
        {
            "type": "rbac_group_member",
            "group_id": "rbac_group_03Yh4MjXsQe7Rv2BnKt9Wz5D",
            "user_id": "user_Oov3aYewo6ZuoGh8thaiV1uNoy1aXe",
            "email": "mbsimpson@simpson.corp",
            "created_at": "2025-04-04T09:00:00.000000Z",
        },
    ],
}
