SENTRY_ALERT_RULES = [
    {
        "id": "500",
        "name": "High Error Rate",
        "dateCreated": "2024-02-10T10:00:00.000Z",
        "actionMatch": "all",
        "filterMatch": "all",
        "frequency": 1800,
        "environment": "production",
        "status": "active",
    },
    {
        "id": "501",
        "name": "New Issue Alert",
        "dateCreated": "2024-02-11T10:00:00.000Z",
        "actionMatch": "any",
        "filterMatch": "any",
        "frequency": 3600,
        "environment": None,
        "status": "active",
    },
]
