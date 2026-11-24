from typing import Any

MOCK_WORKSPACE_RAW: dict[str, Any] = {
    "uuid": "{workspace-uuid-1}",
    "slug": "my-workspace",
    "name": "My Workspace",
    "is_private": True,
    "created_on": "2020-01-01T00:00:00.000000+00:00",
    "links": {"html": {"href": "https://bitbucket.org/my-workspace"}},
}

MOCK_WORKSPACES: dict[str, Any] = {
    "values": [MOCK_WORKSPACE_RAW],
    "next": None,
}

TEST_WORKSPACE_ID = "workspace-uuid-1"
TEST_WORKSPACE_SLUG = "my-workspace"
