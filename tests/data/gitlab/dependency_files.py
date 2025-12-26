"""Test data for GitLab dependency files module."""

# Raw GitLab API response format - matches what repository tree search finds
GET_GITLAB_DEPENDENCY_FILES_RESPONSE = [
    {
        "name": "package.json",
        "path": "package.json",
        "type": "100644",
        "id": "abc123def456",
    },
    {
        "name": "requirements.txt",
        "path": "backend/requirements.txt",
        "type": "100644",
        "id": "def456ghi789",
    },
    {
        "name": "go.mod",
        "path": "services/api/go.mod",
        "type": "100644",
        "id": "ghi789jkl012",
    },
]

TEST_PROJECT_URL = "https://gitlab.example.com/myorg/awesome-project"

# Expected transformed dependency files output
TRANSFORMED_DEPENDENCY_FILES = [
    {
        "id": "https://gitlab.example.com/myorg/awesome-project/blob/package.json",
        "path": "package.json",
        "filename": "package.json",
        "project_url": TEST_PROJECT_URL,
    },
    {
        "id": "https://gitlab.example.com/myorg/awesome-project/blob/backend/requirements.txt",
        "path": "backend/requirements.txt",
        "filename": "requirements.txt",
        "project_url": TEST_PROJECT_URL,
    },
    {
        "id": "https://gitlab.example.com/myorg/awesome-project/blob/services/api/go.mod",
        "path": "services/api/go.mod",
        "filename": "go.mod",
        "project_url": TEST_PROJECT_URL,
    },
]
