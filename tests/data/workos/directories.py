class MockDirectory:
    """Mock WorkOS Directory object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data["name"]
        self.domain = data["domain"]
        self.state = data["state"]
        self.type = data["type"]
        self.organization_id = data["organization_id"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]


WORKOS_DIRECTORIES = [
    MockDirectory(
        {
            "id": "dir_01HXYZ1234567890ABCDEFGHIJ",
            "name": "Springfield Azure AD",
            "domain": "springfield.com",
            "state": "linked",
            "type": "azure scim v2.0",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
        }
    ),
]
