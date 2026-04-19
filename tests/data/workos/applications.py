class MockRedirectUri:
    """Mock WorkOS RedirectUri object for testing."""

    def __init__(self, uri: str, default: bool = False):
        self.uri = uri
        self.default = default


class MockConnectApplication:
    """Mock WorkOS ConnectApplication object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.client_id = data["client_id"]
        self.name = data["name"]
        self.description = data.get("description")
        self.application_type = data["application_type"]
        self.organization_id = data.get("organization_id")
        self.scopes = data.get("scopes", [])
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]
        self.redirect_uris = (
            [MockRedirectUri(u) for u in data["redirect_uris"]]
            if data.get("redirect_uris")
            else None
        )
        self.uses_pkce = data.get("uses_pkce")
        self.is_first_party = data.get("is_first_party")
        self.was_dynamically_registered = data.get("was_dynamically_registered")


WORKOS_APPLICATIONS = [
    MockConnectApplication(
        {
            "id": "conn_app_01HXYZ1111111111AAAAAAAA",
            "client_id": "client_app_oauth_001",
            "name": "Springfield Portal",
            "description": "Employee self-service portal",
            "application_type": "oauth",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "scopes": ["openid", "profile", "email"],
            "created_at": "2024-10-01T10:00:00.000000Z",
            "updated_at": "2024-10-05T12:00:00.000000Z",
            "redirect_uris": ["https://portal.springfield.example.com/callback"],
            "uses_pkce": True,
            "is_first_party": True,
            "was_dynamically_registered": False,
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
            "redirect_uris": None,
            "uses_pkce": None,
            "is_first_party": False,
            "was_dynamically_registered": False,
        },
    ),
]
