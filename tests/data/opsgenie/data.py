ACCOUNT = {
    "name": "example-account",
    "userCount": 2,
    "plan": {"name": "Example", "maxUserCount": 10},
}

TEAMS = [
    {"id": "team-1", "name": "Platform", "description": "Platform team"},
    {"id": "team-2", "name": "Payments", "description": "Payments team"},
]

USERS = [
    {
        "id": "user-1",
        "username": "alice@example.com",
        "fullName": "Alice Example",
        "role": {"name": "User"},
        "blocked": False,
        "verified": True,
        "timeZone": "America/Los_Angeles",
        "locale": "en_US",
        "createdAt": "2026-01-01T00:00:00Z",
    },
    {
        "id": "user-2",
        "username": "bob@example.com",
        "fullName": "Bob Example",
        "role": {"name": "Admin"},
        "blocked": False,
        "verified": True,
        "timeZone": "Europe/London",
        "locale": "en_GB",
        "createdAt": "2026-01-02T00:00:00Z",
    },
]

SCHEDULES = [
    {
        "id": "schedule-1",
        "name": "Platform Primary",
        "description": "Primary platform rotation",
        "timezone": "America/Los_Angeles",
        "enabled": True,
        "ownerTeam": {"id": "team-1", "name": "Platform"},
    },
    {
        "id": "schedule-2",
        "name": "Payments Primary",
        "description": "Primary payments rotation",
        "timezone": "Europe/London",
        "enabled": True,
        "ownerTeam": {"id": "team-2", "name": "Payments"},
    },
]
