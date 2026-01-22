TEST_PROJECT_ID = "test-project-123"

LIST_SECRETS_RESPONSE = [
    {
        "name": "projects/test-project-123/secrets/my-api-key",
        "createTime": "2024-01-15T10:30:00Z",
        "replication": {
            "automatic": {},
        },
        "etag": "abc123",
        "labels": {
            "env": "production",
            "team": "platform",
        },
    },
    {
        "name": "projects/test-project-123/secrets/db-password",
        "createTime": "2024-02-20T14:00:00Z",
        "expireTime": "2025-02-20T14:00:00Z",
        "replication": {
            "userManaged": {
                "replicas": [
                    {"location": "us-central1"},
                    {"location": "us-east1"},
                ],
            },
        },
        "etag": "def456",
        "rotation": {
            "rotationPeriod": "2592000s",
            "nextRotationTime": "2024-03-20T14:00:00Z",
        },
        "labels": {
            "env": "production",
        },
    },
]

# Map secret names to their versions (as returned by the API)
SECRET_VERSIONS_BY_SECRET = {
    "projects/test-project-123/secrets/my-api-key": [
        {
            "name": "projects/test-project-123/secrets/my-api-key/versions/1",
            "createTime": "2024-01-15T10:30:00Z",
            "state": "ENABLED",
            "etag": "ver1abc",
        },
        {
            "name": "projects/test-project-123/secrets/my-api-key/versions/2",
            "createTime": "2024-01-20T08:00:00Z",
            "state": "ENABLED",
            "etag": "ver2abc",
        },
    ],
    "projects/test-project-123/secrets/db-password": [
        {
            "name": "projects/test-project-123/secrets/db-password/versions/1",
            "createTime": "2024-02-20T14:00:00Z",
            "state": "DISABLED",
            "etag": "ver1def",
        },
        {
            "name": "projects/test-project-123/secrets/db-password/versions/2",
            "createTime": "2024-02-25T09:00:00Z",
            "destroyTime": "2024-03-01T12:00:00Z",
            "state": "DESTROYED",
            "etag": "ver2def",
        },
        {
            "name": "projects/test-project-123/secrets/db-password/versions/3",
            "createTime": "2024-03-01T10:00:00Z",
            "state": "ENABLED",
            "etag": "ver3def",
        },
    ],
}
