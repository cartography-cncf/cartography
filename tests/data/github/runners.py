"""Test data for GitHub self-hosted runners."""

GET_ORG_RUNNERS = [
    {
        "id": 23,
        "name": "linux-runner",
        "os": "linux",
        "status": "online",
        "busy": True,
        "ephemeral": False,
        "labels": [
            {"id": 5, "name": "self-hosted", "type": "read-only"},
            {"id": 7, "name": "X64", "type": "read-only"},
            {"id": 11, "name": "Linux", "type": "read-only"},
        ],
    },
    {
        "id": 24,
        "name": "mac-runner",
        "os": "macos",
        "status": "offline",
        "busy": False,
        "ephemeral": False,
        "labels": [
            {"id": 5, "name": "self-hosted", "type": "read-only"},
            {"id": 7, "name": "X64", "type": "read-only"},
            {"id": 20, "name": "macOS", "type": "read-only"},
            {"id": 21, "name": "no-gpu", "type": "custom"},
        ],
    },
]

GET_REPO_RUNNERS = [
    GET_ORG_RUNNERS[0],
    {
        "id": 25,
        "name": "repo-only-runner",
        "os": "linux",
        "status": "online",
        "busy": False,
        "ephemeral": True,
        "labels": [
            {"id": 5, "name": "self-hosted", "type": "read-only"},
            {"id": 11, "name": "Linux", "type": "read-only"},
            {"id": 31, "name": "deploy", "type": "custom"},
        ],
    },
]
