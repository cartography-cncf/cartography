class MockSlimRole:
    """Mock WorkOS SlimRole object for testing."""

    def __init__(self, slug: str):
        self.slug = slug


class MockOrganizationMembership:
    """Mock WorkOS Organization Membership object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.user_id = data["user_id"]
        self.organization_id = data["organization_id"]
        self.status = data["status"]
        self.role = MockSlimRole(data["role"]["slug"])
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]


WORKOS_ORGANIZATION_MEMBERSHIPS = [
    MockOrganizationMembership(
        {
            "id": "om_01HXYZ1234567890ABCDEFGHIJ",
            "user_id": "user_01HXYZ1234567890ABCDEFGHIJ",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "status": "active",
            "role": {"slug": "admin"},
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
        }
    ),
    MockOrganizationMembership(
        {
            "id": "om_02HXYZ0987654321ZYXWVUTSRQ",
            "user_id": "user_02HXYZ0987654321ZYXWVUTSRQ",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "status": "active",
            "role": {"slug": "member"},
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
        }
    ),
]
