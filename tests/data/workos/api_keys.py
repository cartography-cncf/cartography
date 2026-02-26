class MockApiKeyOwner:
    """Mock WorkOS API Key Owner object for testing."""

    def __init__(self, data: dict):
        self.type = data["type"]
        self.id = data["id"]


class MockApiKey:
    """Mock WorkOS API Key object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data["name"]
        self.obfuscated_value = data.get("obfuscated_value")
        self.permissions = data.get("permissions", [])
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]
        self.last_used_at = data.get("last_used_at")
        self.owner = MockApiKeyOwner(data["owner"]) if data.get("owner") else None


WORKOS_API_KEYS = [
    MockApiKey(
        {
            "id": "api_key_01HXYZ1111111111AAAAAAAA",
            "name": "Reactor Monitoring Key",
            "obfuscated_value": "sk_...abc1",
            "permissions": ["read:users", "read:organizations"],
            "created_at": "2024-11-01T10:00:00.000000Z",
            "updated_at": "2024-11-05T12:00:00.000000Z",
            "last_used_at": "2024-11-10T08:30:00.000000Z",
            "owner": {
                "type": "organization",
                "id": "org_01HXYZ1234567890ABCDEFGHIJ",
            },
        }
    ),
    MockApiKey(
        {
            "id": "api_key_02HXYZ2222222222BBBBBBBB",
            "name": "Squishee Machine Key",
            "obfuscated_value": "sk_...xyz2",
            "permissions": ["read:users"],
            "created_at": "2024-11-02T14:00:00.000000Z",
            "updated_at": "2024-11-06T16:00:00.000000Z",
            "last_used_at": None,
            "owner": {
                "type": "organization",
                "id": "org_02HXYZ0987654321ZYXWVUTSRQ",
            },
        }
    ),
]
