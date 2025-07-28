from msgraph.generated.models.group import Group
from msgraph.generated.models.user import User

TEST_TENANT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c479"
TEST_CLIENT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c479"
TEST_CLIENT_SECRET = "abcdefghijklmnopqrstuvwxyz"

MOCK_ENTRA_GROUPS = [
    Group(
        id="11111111-1111-1111-1111-111111111111",
        odata_type="#microsoft.graph.group",
        display_name="Security Team",
        description="Security group",
        mail="security@example.com",
        mail_enabled=True,
        mail_nickname="security",
        security_enabled=True,
        group_types=["Unified"],
        visibility="Private",
    ),
    Group(
        id="22222222-2222-2222-2222-222222222222",
        odata_type="#microsoft.graph.group",
        display_name="Developers",
        mail="devs@example.com",
        mail_enabled=False,
        mail_nickname="devs",
        security_enabled=True,
        group_types=["DynamicMembership"],
        visibility="Public",
    ),
]

MOCK_GROUP_MEMBERS = {
    "11111111-1111-1111-1111-111111111111": [
        User(
            id="ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
            odata_type="#microsoft.graph.user",
            display_name="Homer Simpson",
        ),
        User(
            id="11dca63b-cb03-4e53-bb75-fa8060285550",
            odata_type="#microsoft.graph.user",
            display_name="Entra Test User 1",
        ),
        Group(
            id="22222222-2222-2222-2222-222222222222",
            odata_type="#microsoft.graph.group",
            display_name="Developers",
        ),
    ],
    "22222222-2222-2222-2222-222222222222": [],
}

MOCK_GROUP_OWNERS = {
    "11111111-1111-1111-1111-111111111111": [
        User(
            id="ae4ac864-4433-4ba6-96a6-20f8cffdadcb",
            odata_type="#microsoft.graph.user",
            display_name="Homer Simpson",
        ),
    ],
    "22222222-2222-2222-2222-222222222222": [
        User(
            id="11dca63b-cb03-4e53-bb75-fa8060285550",
            odata_type="#microsoft.graph.user",
            display_name="Entra Test User 1",
        ),
    ],
}
