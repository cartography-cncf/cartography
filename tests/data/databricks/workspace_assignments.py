# Keyed by numeric workspace id, mirroring the account permissionassignments API.
DATABRICKS_WORKSPACE_ASSIGNMENTS = {
    "1234567890123456": {
        "permission_assignments": [
            {
                "principal": {
                    "principal_id": 410001,
                    "user_name": "jeremy@subimage.io",
                },
                "permissions": ["ADMIN"],
            },
            {
                "principal": {
                    "principal_id": 310002,
                    "group_name": "admins",
                },
                "permissions": ["USER"],
            },
        ],
    },
    "6543210987654321": {
        "permission_assignments": [
            {
                "principal": {
                    "principal_id": 510001,
                    "service_principal_name": "abcd1234-5678-90ab-cdef-1234567890ab",
                },
                "permissions": ["USER"],
            },
        ],
    },
}
