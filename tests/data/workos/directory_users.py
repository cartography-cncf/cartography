class MockDirectoryGroup:
    """Mock WorkOS Directory Group object for testing."""

    def __init__(self, group_id: str):
        self.id = group_id


class MockDirectoryUser:
    """Mock WorkOS Directory User object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.idp_id = data["idp_id"]
        self.directory_id = data["directory_id"]
        self.organization_id = data["organization_id"]
        self.first_name = data["first_name"]
        self.last_name = data["last_name"]
        self.email = data["email"]
        self.state = data["state"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]
        self.custom_attributes = data.get("custom_attributes")
        self.raw_attributes = data.get("raw_attributes")
        self.role = data.get("role")
        # Convert group_ids list to list of MockDirectoryGroup objects
        self.groups = [MockDirectoryGroup(gid) for gid in data.get("group_ids", [])]


WORKOS_DIRECTORY_USERS = [
    MockDirectoryUser(
        {
            "id": "dirusr_01HXYZ1234567890ABCDEFGHIJ",
            "idp_id": "azure_user_123",
            "directory_id": "dir_01HXYZ1234567890ABCDEFGHIJ",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "first_name": "Homer",
            "last_name": "Simpson",
            "email": "hjsimpson@springfield.com",
            "state": "active",
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
            "custom_attributes": {},
            "raw_attributes": {},
            "role": None,
            "group_ids": ["dirgrp_01HXYZ1234567890ABCDEFGHIJ"],
        }
    ),
    MockDirectoryUser(
        {
            "id": "dirusr_02HXYZ0987654321ZYXWVUTSRQ",
            "idp_id": "azure_user_456",
            "directory_id": "dir_01HXYZ1234567890ABCDEFGHIJ",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "first_name": "Marge",
            "last_name": "Simpson",
            "email": "mbsimpson@springfield.com",
            "state": "active",
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
            "custom_attributes": {},
            "raw_attributes": {},
            "role": None,
            "group_ids": ["dirgrp_02HXYZ0987654321ZYXWVUTSRQ"],
        }
    ),
]
