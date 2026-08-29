class MockApplicationCredentialsListItem:
    """Mock WorkOS ApplicationCredentialsListItem object for testing."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.secret_hint = data["secret_hint"]
        self.last_used_at = data.get("last_used_at")
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]


WORKOS_APPLICATION_CLIENT_SECRETS_BY_APP = {
    "conn_app_01HXYZ1111111111AAAAAAAA": [
        MockApplicationCredentialsListItem(
            {
                "id": "secret_01HXYZAAAA1111111111AAAA",
                "secret_hint": "...abc1",
                "last_used_at": "2024-10-10T08:00:00.000000Z",
                "created_at": "2024-10-01T10:00:00.000000Z",
                "updated_at": "2024-10-10T08:00:00.000000Z",
            },
        ),
    ],
    "conn_app_02HXYZ2222222222BBBBBBBB": [
        MockApplicationCredentialsListItem(
            {
                "id": "secret_02HXYZBBBB2222222222BBBB",
                "secret_hint": "...xyz9",
                "last_used_at": None,
                "created_at": "2024-10-02T14:00:00.000000Z",
                "updated_at": "2024-10-02T14:00:00.000000Z",
            },
        ),
        MockApplicationCredentialsListItem(
            {
                "id": "secret_02HXYZCCCC3333333333CCCC",
                "secret_hint": "...def2",
                "last_used_at": "2024-10-11T09:00:00.000000Z",
                "created_at": "2024-10-03T15:00:00.000000Z",
                "updated_at": "2024-10-11T09:00:00.000000Z",
            },
        ),
    ],
}
