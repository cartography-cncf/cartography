class MockUser:
    """Mock WorkOS User object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.email = data["email"]
        self.first_name = data["first_name"]
        self.last_name = data["last_name"]
        self.email_verified = data["email_verified"]
        self.profile_picture_url = data.get("profile_picture_url")
        self.last_sign_in_at = data.get("last_sign_in_at")
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]


WORKOS_USERS = [
    MockUser(
        {
            "id": "user_01HXYZ1234567890ABCDEFGHIJ",
            "email": "hjsimpson@springfield.com",
            "first_name": "Homer",
            "last_name": "Simpson",
            "email_verified": True,
            "profile_picture_url": "https://example.com/homer.jpg",
            "last_sign_in_at": "2024-11-05T10:30:00.000000Z",
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
        }
    ),
    MockUser(
        {
            "id": "user_02HXYZ0987654321ZYXWVUTSRQ",
            "email": "mbsimpson@springfield.com",
            "first_name": "Marge",
            "last_name": "Simpson",
            "email_verified": True,
            "profile_picture_url": "https://example.com/marge.jpg",
            "last_sign_in_at": "2024-11-04T14:20:00.000000Z",
            "created_at": "2024-10-30T23:58:27.427722Z",
            "updated_at": "2024-11-01T23:59:27.427722Z",
        }
    ),
]
