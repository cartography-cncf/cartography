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
SIGNIN = {
    "email": "alice@example.com",
    "time": "2026-09-29T12:00:00Z",
    "type": "Sign in",
    "client_type": "Browser",
    "version": "6.1.0",
    "ip_address": "192.0.2.1",
}
SESSION = {
    "uuid": "/session//one",
    "id": 12345678901,
    "email": "alice@example.com",
    "start_time": "2026-09-29T12:00:00Z",
    "end_time": "2026-09-29T12:01:00Z",
    "participants": 1,
}
PARTICIPANT = {
    "user_id": "1",
    "participant_user_id": "user-1",
    "join_time": "2026-09-29T12:00:00Z",
    "leave_time": "2026-09-29T12:01:00Z",
    "role": "host",
    "device": "Mac",
    "version": "6.1.0",
}
