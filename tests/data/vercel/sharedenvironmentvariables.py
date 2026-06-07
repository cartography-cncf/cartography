VERCEL_SHARED_ENVIRONMENT_VARIABLES = [
    {
        "id": "senv_123",
        "key": "SHARED_SECRET",
        "type": "encrypted",
        "target": ["production", "preview", "development"],
        "createdAt": 1640995200000,
        "updatedAt": 1641081600000,
    },
    {
        "id": "senv_456",
        "key": "SENTRY_DSN",
        "type": "plain",
        "target": ["production"],
        "createdAt": 1641000000000,
        "updatedAt": 1641100000000,
    },
]
