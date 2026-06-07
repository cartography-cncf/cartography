class MockConnectApplication:
    """Mock WorkOS ConnectApplication object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.client_id = data["client_id"]
        self.name = data["name"]
        self.description = data.get("description")
        self.application_type = data.get("application_type")
        self.organization_id = data.get("organization_id")
        self.scopes = data.get("scopes", [])
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]


WORKOS_APPLICATIONS = [
    MockConnectApplication(
        {
            "id": "conn_app_01HXYZ1111111111AAAAAAAA",
            "client_id": "client_app_oauth_001",
            "name": "Springfield Portal",
            "description": "Employee self-service portal",
            # OAuth apps: application_type not set in v6
            "application_type": None,
            "organization_id": None,
            "scopes": ["openid", "profile", "email"],
            "created_at": "2024-10-01T10:00:00.000000Z",
            "updated_at": "2024-10-05T12:00:00.000000Z",
        },
    ),
    MockConnectApplication(
        {
            "id": "conn_app_02HXYZ2222222222BBBBBBBB",
            "client_id": "client_app_m2m_001",
            "name": "Squishee Inventory Sync",
            "description": "M2M integration for inventory",
            "application_type": "m2m",
            "organization_id": "org_02HXYZ0987654321ZYXWVUTSRQ",
            "scopes": ["inventory:read", "inventory:write"],
            "created_at": "2024-10-02T14:00:00.000000Z",
            "updated_at": "2024-10-06T16:00:00.000000Z",
        },
    ),
]
