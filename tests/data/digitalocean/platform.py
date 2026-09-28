from typing import Any

ACCOUNT_RESPONSE: dict[str, Any] = {
    "account": {
        "droplet_limit": 10,
        "floating_ip_limit": 10,
        "reserved_ip_limit": 10,
        "volume_limit": 5000,
        "email": "test@email.com",
        "name": "Zach Saucier",
        "uuid": "test-account-uuid",
        "email_verified": True,
        "status": "active",
        "status_message": "",
        "team": {"uuid": "test-owner-uuid", "name": "My Team"},
    }
}
