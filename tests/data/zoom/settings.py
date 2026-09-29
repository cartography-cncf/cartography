from typing import Any

SETTINGS_RESPONSES: dict[str, dict[str, Any]] = {
    "default": {
        "in_meeting": {
            "file_transfer": False,
            "screen_sharing": True,
            "who_can_share_screen": "host",
        },
        "schedule_meeting": {
            "join_before_host": False,
            "pmi_password": "synthetic-secret-not-for-ingestion",
            "default_password_for_scheduled_meetings": "synthetic-secret-not-for-ingestion",
        },
        "recording": {
            "cloud_recording": True,
            "local_recording": False,
            "allow_share": True,
            "embed_passcode_in_shareable_link": False,
        },
        "unknown_security_setting": {"secret": "synthetic-secret-not-for-ingestion"},
    },
    "security": {
        "security": {
            "sign_in_with_two_factor_auth": "all",
            "signin_with_sso": {
                "enable": True,
                "require_sso_for_domains": True,
                "domains": ["example.com"],
            },
        }
    },
    "meeting_security": {
        "meeting_security": {
            "waiting_room": True,
            "auto_security": True,
            "meeting_password": True,
            "pmi_password": True,
            "end_to_end_encrypted_meetings": True,
            "encryption_type": "e2ee",
        }
    },
    "meeting_authentication": {
        "meeting_authentication": True,
        "allow_authentication_exception": False,
        "authentication_options": [
            {
                "id": "profile-one",
                "domains": "example.com",
                "type": "enforce_login_with_domains",
            }
        ],
    },
    "recording_authentication": {"recording_authentication": True},
}

LOCKED_SETTINGS_RESPONSES: dict[str, dict[str, Any]] = {
    "default": {
        "schedule_meeting": {"meeting_authentication": True, "join_before_host": False},
        "recording": {"recording_authentication": True, "cloud_recording": False},
    },
    "meeting_security": {
        "meeting_security": {"waiting_room": True, "encryption_type": True}
    },
}
