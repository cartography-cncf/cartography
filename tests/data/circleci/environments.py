# Raw items of GET /deploy/environments?org-id=...
CIRCLECI_ENVIRONMENTS = [
    {
        "id": "env-1",
        "name": "production",
        "description": "Prod environment",
        "labels": ["prod"],
        "created_at": "2021-09-08T10:00:00Z",
        "updated_at": "2021-09-08T10:00:00Z",
    },
]

# Raw items of GET /deploy/components?org-id=...
CIRCLECI_COMPONENTS = [
    {
        "id": "comp-1",
        "name": "web-service",
        "project_id": "proj-1",
        "labels": ["service"],
        "release_count": 12,
        "created_at": "2021-09-08T10:00:00Z",
        "updated_at": "2021-09-08T10:00:00Z",
    },
]
