class MockOrganizationDomain:
    """Mock WorkOS Organization Domain object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.domain = data["domain"]
        self.organization_id = data["organization_id"]
        self.state = data["state"]
        self.verification_strategy = data["verification_strategy"]
        self.verification_token = data["verification_token"]


WORKOS_ORGANIZATION_DOMAINS = [
    MockOrganizationDomain(
        {
            "id": "orgdom_01HXYZ1234567890ABCDEFGHIJ",
            "domain": "springfield.com",
            "organization_id": "org_01HXYZ1234567890ABCDEFGHIJ",
            "state": "verified",
            "verification_strategy": "dns",
            "verification_token": "workos_verification_123456",
        }
    ),
]
