USERS = [
    {
        "object": "user",
        "id": "person-1",
        "type": "person",
        "name": "Alice Example",
        "avatar_url": None,
        "person": {"email": "ALICE@example.com"},
    },
    {
        "object": "user",
        "id": "person-2",
        "type": "person",
        "name": "Bob Example",
        "avatar_url": None,
        "person": {},
    },
    {
        "object": "user",
        "id": "bot-1",
        "type": "bot",
        "name": "Security Exporter",
        "avatar_url": None,
        "bot": {
            "owner": {
                "type": "user",
                "user": {"object": "user", "id": "person-1"},
            },
        },
    },
    {
        "object": "user",
        "id": "bot-2",
        "type": "bot",
        "name": "Workspace Bot",
        "avatar_url": None,
        "bot": {"owner": {"type": "workspace", "workspace": True}},
    },
]
