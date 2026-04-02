SENTRY_MEMBERS = [
    {
        "id": "300",
        "email": "mbsimpson@simpson.corp",
        "name": "Marge Simpson",
        "orgRole": "owner",
        "dateCreated": "2024-01-15T10:00:00.000Z",
        "pending": False,
        "expired": False,
        "user": {
            "id": "u-300",
            "username": "mbsimpson@simpson.corp",
            "has2fa": True,
        },
    },
    {
        "id": "301",
        "email": "hjsimpson@simpson.corp",
        "name": "Homer Simpson",
        "orgRole": "member",
        "dateCreated": "2024-01-16T10:00:00.000Z",
        "pending": False,
        "expired": False,
        "user": {
            "id": "u-301",
            "username": "hjsimpson@simpson.corp",
            "has2fa": False,
        },
    },
]

# Mapping returned by _get_team_memberships: member_id -> [(team_id, role), ...]
SENTRY_TEAM_MEMBERSHIPS = {
    "301": [("200", "admin"), ("201", "contributor")],
}
