VERCEL_WEBHOOKS = [
    {
        "id": "whk_123",
        "url": "https://hooks.example.com/vercel",
        "events": ["deployment.created", "deployment.succeeded"],
        "projectIds": ["prj_abc"],
        "createdAt": 1640995200000,
        "updatedAt": 1641081600000,
    },
    {
        "id": "whk_456",
        "url": "https://hooks.example.org/vercel",
        "events": ["deployment.error"],
        "projectIds": ["prj_abc"],
        "createdAt": 1641000000000,
        "updatedAt": 1641100000000,
    },
]
