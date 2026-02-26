class MockRole:
    """Mock WorkOS Role object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.slug = data["slug"]
        self.name = data["name"]
        self.description = data.get("description")
        self.type = data["type"]
        self.organization_id = data.get("organization_id")
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]


WORKOS_ROLES = [
    MockRole(
        {
            "id": "role_01HXYZ1234567890ABCDEFGHIJ",
            "slug": "admin",
            "name": "Administrator",
            "description": "Full access to all resources",
            "type": "environment",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
        }
    ),
    MockRole(
        {
            "id": "role_02HXYZ0987654321ZYXWVUTSRQ",
            "slug": "member",
            "name": "Member",
            "description": "Standard member access",
            "type": "organization",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
        }
    ),
]
