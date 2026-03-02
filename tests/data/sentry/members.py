SENTRY_MEMBERS = [
    {
        "id": "300",
        "email": "mbsimpson@simpson.corp",
        "name": "Marge Simpson",
        "orgRole": "admin",
        "dateCreated": "2024-01-15T10:00:00.000Z",
        "pending": False,
        "expired": False,
        "user": {
            "id": "u-300",
            "username": "mbsimpson@simpson.corp",
            "has2fa": True,
        },
        "teamRoles": [
            {"teamSlug": "backend-team", "role": None},
        ],
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
        "teamRoles": [
            {"teamSlug": "backend-team", "role": None},
            {"teamSlug": "frontend-team", "role": None},
        ],
    },
]
