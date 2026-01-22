AIRBYTE_CONNECTIONS = [
    {
        "connectionId": "b9fd93fc-115c-4b5a-a10f-833280713819",
        "name": "Backup to S3",
        "sourceId": "b626221b-9250-4c8b-8615-653ca7e807ab",
        "destinationId": "30e064ed-4211-4868-9b8f-e2bbc8f8969a",
        "workspaceId": "e4388e31-9c21-461b-9b5d-1905ca28c599",
        "status": "active",
        "schedule": {"scheduleType": "basic", "basicTiming": "Every 24 HOURS"},
        "dataResidency": "us",
        "configurations": {
            "streams": [
                {
                    "name": "issues",
                    "syncMode": "full_refresh_overwrite",
                    "cursorField": ["updated_at"],
                    "primaryKey": [["id"]],
                    "includeFiles": False,
                    "selectedFields": [],
                    "mappers": [],
                },
                {
                    "name": "users",
                    "syncMode": "full_refresh_overwrite",
                    "cursorField": [],
                    "primaryKey": [["id"]],
                    "includeFiles": False,
                    "selectedFields": [],
                    "mappers": [],
                },
            ]
        },
        "createdAt": 1748426557,
        "tags": [
            {
                "tagId": "f367d42e-4987-41af-9388-c96f6237a798",
                "workspaceId": "e4388e31-9c21-461b-9b5d-1905ca28c599",
                "name": "sensitive",
                "color": "75DCFF",
            }
        ],
        "nonBreakingSchemaUpdatesBehavior": "propagate_columns",
        "namespaceDefinition": "destination",
        "prefix": "",
    }
]
