class MockDirectoryGroup:
    """Mock WorkOS Directory Group object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.idp_id = data["idp_id"]
        self.directory_id = data["directory_id"]
        self.organization_id = data["organization_id"]
        self.name = data["name"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]
        self.raw_attributes = data.get("raw_attributes")


WORKOS_DIRECTORY_GROUPS = [
    MockDirectoryGroup(
        {
            "id": "dirgrp_01HXYZ1234567890ABCDEFGHIJ",
            "idp_id": "azure_group_123",
            "directory_id": "dir_01HXYZ1234567890ABCDEFGHIJ",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "name": "Engineering",
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
            "raw_attributes": {},
        }
    ),
    MockDirectoryGroup(
        {
            "id": "dirgrp_02HXYZ0987654321ZYXWVUTSRQ",
            "idp_id": "azure_group_456",
            "directory_id": "dir_01HXYZ1234567890ABCDEFGHIJ",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "name": "Management",
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
            "raw_attributes": {},
        }
    ),
]
