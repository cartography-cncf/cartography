LIST_API_KEYS_RESPONSE = [
    {
        "name": "projects/test-project-123/locations/global/keys/key-abc",
        "uid": "key-abc",
        "displayName": "Browser key (unrestricted)",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-02T00:00:00Z",
        "etag": "etag-abc",
    },
    {
        "name": "projects/test-project-123/locations/global/keys/key-def",
        "uid": "key-def",
        "displayName": "Maps key (restricted)",
        "createTime": "2024-02-01T00:00:00Z",
        "updateTime": "2024-02-02T00:00:00Z",
        "restrictions": {
            "apiTargets": [{"service": "maps-backend.googleapis.com"}],
        },
        "etag": "etag-def",
    },
]
