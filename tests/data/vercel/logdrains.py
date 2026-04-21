VERCEL_LOG_DRAINS = [
    {
        "id": "ld_123",
        "name": "Datadog Logs",
        "url": "https://http-intake.logs.datadoghq.com",
        "deliveryFormat": "json",
        "status": "enabled",
        "sources": ["build", "lambda"],
        "environments": ["production"],
        "projectIds": ["prj_def"],
        "createdAt": 1640995200000,
    },
    {
        "id": "ld_456",
        "name": "S3 Archive",
        "url": "https://s3.amazonaws.com/logs-bucket",
        "deliveryFormat": "ndjson",
        "status": "disabled",
        "sources": ["static", "edge"],
        "environments": ["preview"],
        "projectIds": ["prj_def"],
        "createdAt": 1641081600000,
    },
]
