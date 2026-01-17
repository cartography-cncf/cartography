"""Test data for GitLab branches module."""

# Raw GitLab API response format - matches what /projects/:id/repository/branches returns
GET_GITLAB_BRANCHES_RESPONSE = [
    {
        "name": "main",
        "protected": True,
        "default": True,
        "web_url": "https://gitlab.example.com/myorg/awesome-project/-/tree/main",
        "commit": {
            "id": "abc123def456",
            "title": "Latest commit",
        },
    },
    {
        "name": "develop",
        "protected": True,
        "default": False,
        "web_url": "https://gitlab.example.com/myorg/awesome-project/-/tree/develop",
        "commit": {
            "id": "def456ghi789",
            "title": "Feature work",
        },
    },
    {
        "name": "feature/new-api",
        "protected": False,
        "default": False,
        "web_url": "https://gitlab.example.com/myorg/awesome-project/-/tree/feature/new-api",
        "commit": {
            "id": "ghi789jkl012",
            "title": "Add new API endpoint",
        },
    },
]

TEST_PROJECT_URL = "https://gitlab.example.com/myorg/awesome-project"

# Expected transformed branches output
TRANSFORMED_BRANCHES = [
    {
        "id": "https://gitlab.example.com/myorg/awesome-project/tree/main",
        "name": "main",
        "protected": True,
        "default": True,
        "web_url": "https://gitlab.example.com/myorg/awesome-project/-/tree/main",
        "project_url": TEST_PROJECT_URL,
    },
    {
        "id": "https://gitlab.example.com/myorg/awesome-project/tree/develop",
        "name": "develop",
        "protected": True,
        "default": False,
        "web_url": "https://gitlab.example.com/myorg/awesome-project/-/tree/develop",
        "project_url": TEST_PROJECT_URL,
    },
    {
        "id": "https://gitlab.example.com/myorg/awesome-project/tree/feature/new-api",
        "name": "feature/new-api",
        "protected": False,
        "default": False,
        "web_url": "https://gitlab.example.com/myorg/awesome-project/-/tree/feature/new-api",
        "project_url": TEST_PROJECT_URL,
    },
]
