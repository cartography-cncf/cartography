"""Test data for GitLab organizations module."""

# Raw GitLab API response format - matches what /groups/:id returns for a top-level group
GET_GITLAB_ORGANIZATION_RESPONSE = {
    "id": 100,
    "name": "MyOrg",
    "path": "myorg",
    "full_path": "myorg",
    "description": "My Organization on GitLab",
    "visibility": "private",
    "web_url": "https://gitlab.example.com/myorg",
    "created_at": "2023-01-01T00:00:00Z",
    "parent_id": None,
}

# Expected transformed organization output
TRANSFORMED_ORGANIZATION = {
    "web_url": "https://gitlab.example.com/myorg",
    "name": "MyOrg",
    "path": "myorg",
    "full_path": "myorg",
    "description": "My Organization on GitLab",
    "visibility": "private",
    "created_at": "2023-01-01T00:00:00Z",
    "gitlab_url": "https://gitlab.example.com",
}
