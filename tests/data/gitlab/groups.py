"""Test data for GitLab groups module."""

# Raw GitLab API response format - matches what /groups/:id/descendant_groups returns
GET_GITLAB_GROUPS_RESPONSE = [
    {
        "id": 20,
        "name": "Platform",
        "path": "platform",
        "full_path": "myorg/platform",
        "description": "Platform engineering team",
        "visibility": "private",
        "web_url": "https://gitlab.example.com/myorg/platform",
        "created_at": "2023-06-15T09:00:00Z",
        "parent_id": 100,  # Parent is the org (not in descendant list)
    },
    {
        "id": 30,
        "name": "Apps",
        "path": "apps",
        "full_path": "myorg/apps",
        "description": "Application development teams",
        "visibility": "internal",
        "web_url": "https://gitlab.example.com/myorg/apps",
        "created_at": "2023-07-20T14:30:00Z",
        "parent_id": 100,  # Parent is the org (not in descendant list)
    },
    {
        "id": 40,
        "name": "Infrastructure",
        "path": "infrastructure",
        "full_path": "myorg/platform/infrastructure",
        "description": "Infrastructure as code",
        "visibility": "private",
        "web_url": "https://gitlab.example.com/myorg/platform/infrastructure",
        "created_at": "2024-01-10T11:00:00Z",
        "parent_id": 20,  # Parent is Platform group
    },
]

TEST_ORG_URL = "https://gitlab.example.com/myorg"

# Expected transformed groups output
TRANSFORMED_GROUPS = [
    {
        "web_url": "https://gitlab.example.com/myorg/platform",
        "name": "Platform",
        "path": "platform",
        "full_path": "myorg/platform",
        "description": "Platform engineering team",
        "visibility": "private",
        "parent_id": 100,
        "created_at": "2023-06-15T09:00:00Z",
        "org_url": TEST_ORG_URL,
        "parent_group_url": None,  # Parent is org, not in group list
    },
    {
        "web_url": "https://gitlab.example.com/myorg/apps",
        "name": "Apps",
        "path": "apps",
        "full_path": "myorg/apps",
        "description": "Application development teams",
        "visibility": "internal",
        "parent_id": 100,
        "created_at": "2023-07-20T14:30:00Z",
        "org_url": TEST_ORG_URL,
        "parent_group_url": None,  # Parent is org, not in group list
    },
    {
        "web_url": "https://gitlab.example.com/myorg/platform/infrastructure",
        "name": "Infrastructure",
        "path": "infrastructure",
        "full_path": "myorg/platform/infrastructure",
        "description": "Infrastructure as code",
        "visibility": "private",
        "parent_id": 20,
        "created_at": "2024-01-10T11:00:00Z",
        "org_url": TEST_ORG_URL,
        "parent_group_url": "https://gitlab.example.com/myorg/platform",  # Nested under Platform
    },
]
