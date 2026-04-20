# Raw /v1/access-groups response, enriched per-group with members + projects
# (as the sync does before transforming). Each project entry carries its per-
# project role (ADMIN | PROJECT_DEVELOPER | PROJECT_VIEWER | PROJECT_GUEST).
VERCEL_RAW_ACCESS_GROUPS = [
    {
        "accessGroupId": "ag_123",
        "name": "Engineering",
        "createdAt": 1640995200000,
        "updatedAt": 1641081600000,
        "membersCount": 2,
        "projectsCount": 1,
        "isDsyncManaged": False,
        "members": [
            {"uid": "user_homer", "email": "homer@example.com"},
            {"uid": "user_marge", "email": "marge@example.com"},
        ],
        "projects": [
            {"projectId": "prj_abc", "role": "PROJECT_DEVELOPER"},
        ],
    },
    {
        "accessGroupId": "ag_456",
        "name": "Admins",
        "createdAt": 1641000000000,
        "updatedAt": 1641100000000,
        "membersCount": 1,
        "projectsCount": 1,
        "isDsyncManaged": True,
        "members": [
            {"uid": "user_homer", "email": "homer@example.com"},
        ],
        "projects": [
            {"projectId": "prj_abc", "role": "ADMIN"},
        ],
    },
]


# Post-transform node shape (for _ensure_local_neo4j_has_test_access_groups).
VERCEL_ACCESS_GROUPS = [
    {
        "accessGroupId": "ag_123",
        "name": "Engineering",
        "createdAt": 1640995200000,
        "updatedAt": 1641081600000,
        "membersCount": 2,
        "projectsCount": 1,
        "isDsyncManaged": False,
        "member_ids": ["user_homer", "user_marge"],
    },
    {
        "accessGroupId": "ag_456",
        "name": "Admins",
        "createdAt": 1641000000000,
        "updatedAt": 1641100000000,
        "membersCount": 1,
        "projectsCount": 1,
        "isDsyncManaged": True,
        "member_ids": ["user_homer"],
    },
]
