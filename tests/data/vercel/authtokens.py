VERCEL_CALLER_USER_ID = "user_homer"

# Raw /v6/user/tokens response shape: `scopes` drives filtering.
# - tok_team   : team-scoped for our test team → kept
# - tok_mixed  : user + team scope including our team → kept
# - tok_other  : team-scoped but for a different team → dropped
# - tok_user   : user-only scope → dropped
VERCEL_RAW_AUTH_TOKENS = [
    {
        "id": "tok_team",
        "name": "CI/CD Token",
        "type": "oauth2",
        "origin": "github-actions",
        "activeAt": 1641081600000,
        "createdAt": 1640995200000,
        "expiresAt": 1672531200000,
        "scopes": [
            {"type": "team", "teamId": "team_abc123", "origin": "github"},
        ],
    },
    {
        "id": "tok_mixed",
        "name": "Personal Access Token",
        "type": "pat",
        "origin": "cli",
        "activeAt": 1641100000000,
        "createdAt": 1641000000000,
        "expiresAt": 1672617600000,
        "scopes": [
            {"type": "user", "origin": "cli"},
            {"type": "team", "teamId": "team_abc123", "origin": "cli"},
        ],
    },
    {
        "id": "tok_other",
        "name": "Other Team Token",
        "type": "pat",
        "origin": "cli",
        "activeAt": 1641100000000,
        "createdAt": 1641000000000,
        "expiresAt": 1672617600000,
        "scopes": [
            {"type": "team", "teamId": "team_other", "origin": "cli"},
        ],
    },
    {
        "id": "tok_user",
        "name": "User-only Token",
        "type": "pat",
        "origin": "cli",
        "activeAt": 1641100000000,
        "createdAt": 1641000000000,
        "expiresAt": 1672617600000,
        "scopes": [
            {"type": "user", "origin": "cli"},
        ],
    },
]

# Shape after transform_tokens(): only team-scoped entries, each stamped with owner_id.
VERCEL_AUTH_TOKENS = [
    {
        "id": "tok_team",
        "name": "CI/CD Token",
        "type": "oauth2",
        "origin": "github-actions",
        "activeAt": 1641081600000,
        "createdAt": 1640995200000,
        "expiresAt": 1672531200000,
        "owner_id": VERCEL_CALLER_USER_ID,
    },
    {
        "id": "tok_mixed",
        "name": "Personal Access Token",
        "type": "pat",
        "origin": "cli",
        "activeAt": 1641100000000,
        "createdAt": 1641000000000,
        "expiresAt": 1672617600000,
        "owner_id": VERCEL_CALLER_USER_ID,
    },
]
