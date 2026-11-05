from typing import Any

MEETING: dict[str, Any] = {
    "id": 12345678901,
    "host_id": "user-1",
    "topic": "Synthetic scheduled meeting",
    "type": 2,
    "status": "waiting",
    "start_time": "2026-09-29T12:00:00Z",
    "created_at": "2026-09-28T12:00:00Z",
    "duration": 30,
    "password": "synthetic-secret",
    "join_url": "https://example.com/meeting?pwd=synthetic-secret",
    "start_url": "https://example.com/start?token=synthetic-secret",
    "agenda": "This free text must not be ingested",
    "settings": {
        "waiting_room": True,
        "meeting_authentication": False,
        "join_before_host": False,
        "approval_type": 2,
        "encryption_type": "enhanced_encryption",
        "auto_recording": "none",
    },
}

RECORDING: dict[str, Any] = {
    "id": 12345678901,
    "uuid": "/synthetic//instance+==",
    "host_id": "user-1",
    "topic": "Synthetic recording",
    "start_time": "2026-09-29T12:00:00Z",
    "duration": 30,
    "total_size": 4096,
    "recording_count": 2,
    "share_url": "https://example.com/recording?pwd=synthetic-secret",
    "recording_play_passcode": "synthetic-secret",
    "recording_files": [
        {
            "id": "file-1",
            "file_type": "MP4",
            "download_url": "https://example.com/video",
        },
        {"file_type": "CC", "download_url": "https://example.com/captions"},
    ],
}

RECORDING_SETTINGS: dict[str, Any] = {
    "password": "synthetic-secret",
    "share_recording": "publicly",
    "recording_authentication": True,
    "authentication_domains": "example.com",
    "on_demand": False,
    "approval_type": 2,
    "viewer_download": False,
    "auto_delete": True,
    "auto_delete_date": "2026-10-29",
}
