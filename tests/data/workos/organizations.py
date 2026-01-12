class MockOrganization:
    """Mock WorkOS Organization object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data["name"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]
        self.allow_profiles_outside_organization = data[
            "allow_profiles_outside_organization"
        ]


WORKOS_ORGANIZATIONS = [
    MockOrganization(
        {
            "id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "name": "Springfield Nuclear Power Plant",
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
            "allow_profiles_outside_organization": False,
        }
    ),
    MockOrganization(
        {
            "id": "org_02HXYZ0987654321ZYXWVUTSRQ",
            "name": "Kwik-E-Mart",
            "created_at": "2024-10-31T12:00:00.000000Z",
            "updated_at": "2024-11-02T08:30:00.000000Z",
            "allow_profiles_outside_organization": True,
        }
    ),
]
