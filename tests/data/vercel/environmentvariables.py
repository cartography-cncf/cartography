VERCEL_ENVIRONMENT_VARIABLES = [
    {
        "id": "env_123",
        "key": "DATABASE_URL",
        "type": "encrypted",
        "target": ["production", "preview"],
        "gitBranch": None,
        "createdAt": 1640995200000,
        "updatedAt": 1641081600000,
        "edgeConfigId": "ecfg_123",
        "comment": "Primary database connection string",
    },
    {
        "id": "env_456",
        "key": "API_KEY",
        "type": "sensitive",
        "target": ["production"],
        "gitBranch": "main",
        "createdAt": 1641000000000,
        "updatedAt": 1641100000000,
        "edgeConfigId": None,
        "comment": "Third-party API key",
    },
]
