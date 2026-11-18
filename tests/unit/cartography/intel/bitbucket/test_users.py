from cartography.intel.bitbucket.users import transform_users
from tests.data.bitbucket.users import MOCK_MEMBERS


def test_transform_users():
    result = transform_users(MOCK_MEMBERS["values"])

    assert result == [
        {
            "account_id": "account-id-1",
            "uuid": "{user-uuid-1}",
            "display_name": "Alice Smith",
            "nickname": "alice",
            "avatar_url": "https://bitbucket.org/account/alice/avatar/",
            "link_html": "https://bitbucket.org/%7Buser-uuid-1%7D/",
        },
    ]
