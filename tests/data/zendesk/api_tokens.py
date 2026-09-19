# Shape from Zendesk's official OpenAPI ListApiTokens example; include_users adds
# creator metadata. These values are fictional, including the excluded secrets.
API_TOKENS = [
    {
        "id": 201,
        "user_id": 101,
        "user_name": "Alice Admin",
        "user_email": "alice@example.com",
        "assigned_user_id": 102,
        "description": "Legacy integration",
        "active": True,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "last_used": "2026-01-02T00:00:00Z",
        "visible_token": "secret-prefix",
        "token": "secret-access-token",
    },
    {
        "id": 202,
        "user_id": 102,
        "description": "Disabled integration",
        "active": False,
        "last_used": None,
    },
    {
        "id": 203,
        "user_id": 103,
        "description": "Former staff integration",
        "active": True,
    },
]
