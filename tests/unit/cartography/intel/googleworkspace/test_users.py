from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.googleworkspace.users
from cartography.intel.googleworkspace.users import sync_googleworkspace_users

_USERS_RESPONSE = [
    {
        "users": [
            {"id": "active-user", "primaryEmail": "a@example.com", "suspended": False},
            {
                "id": "suspended-user",
                "primaryEmail": "s@example.com",
                "suspended": True,
            },
            {"id": "default-user", "primaryEmail": "d@example.com"},
        ],
    },
]


@patch.object(cartography.intel.googleworkspace.users, "cleanup_googleworkspace_users")
@patch.object(cartography.intel.googleworkspace.users, "load_googleworkspace_users")
@patch.object(
    cartography.intel.googleworkspace.users,
    "get_all_users",
    return_value=_USERS_RESPONSE,
)
def test_sync_googleworkspace_users_excludes_suspended(
    _mock_get_all_users, _mock_load, _mock_cleanup
):
    user_ids = sync_googleworkspace_users(
        neo4j_session=MagicMock(),
        admin=MagicMock(),
        googleworkspace_update_tag=12345,
        common_job_parameters={"CUSTOMER_ID": "C123"},
    )

    assert user_ids == ["active-user", "default-user"]
