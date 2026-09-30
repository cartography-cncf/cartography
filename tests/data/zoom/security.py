from typing import Any

ROLES = [{"id": "2", "name": "Member", "total_members": 1}]
GROUPS = [{"id": "group-1", "name": "Engineering", "total_members": 1}]
ROLE_DETAIL = {
    "id": "2",
    "privileges": ["User:Read"],
    "privilege_scopes": [{"permission_id": "User:Read", "group_ids": ["group-1"]}],
}
APP = {
    "app_id": "app-1",
    "app_name": "Inventory",
    "app_developer_type": "THIRD_PARTY",
    "approval_info": {"approved_type": "forAllUser", "app_approval_closed": False},
}
APP_DETAIL = {
    "app_id": "app-1",
    "app_status": "UNPUBLISHED",
    "app_type": "OAuthApp",
    "app_scopes": ["user:read:list_users:admin"],
}
USERS: list[dict[str, Any]] = [
    {
        "id": "account-a:user:user-1",
        "zoom_id": "user-1",
        "email": "alice@example.com",
        "role_id": "2",
        "group_ids": ["group-1"],
        "status": "active",
        "type": 2,
    }
]
