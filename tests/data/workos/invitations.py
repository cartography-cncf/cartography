class MockInvitation:
    """Mock WorkOS Invitation object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.email = data["email"]
        self.state = data["state"]
        self.organization_id = data["organization_id"]
        self.inviter_user_id = data["inviter_user_id"]
        self.token = data.get("token")
        self.accept_invitation_url = data.get("accept_invitation_url")
        self.expires_at = data["expires_at"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]
        self.accepted_at = data.get("accepted_at")
        self.revoked_at = data.get("revoked_at")


WORKOS_INVITATIONS = [
    MockInvitation(
        {
            "id": "inv_01HXYZ1234567890ABCDEFGHIJ",
            "email": "bsimpson@springfield.com",
            "state": "pending",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "inviter_user_id": "user_01HXYZ1234567890ABCDEFGHIJ",
            "token": "Z1234567890ABCDEF",
            "accept_invitation_url": "https://example.com/invitations/Z1234567890ABCDEF",
            "expires_at": "2024-12-01T23:59:59.999999Z",
            "created_at": "2024-11-01T10:00:00.000000Z",
            "updated_at": "2024-11-01T10:00:00.000000Z",
            "accepted_at": None,
            "revoked_at": None,
        }
    ),
]
