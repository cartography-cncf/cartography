"""Test data for GitLab users module."""

TEST_ORG_URL = "https://gitlab.example.com/myorg"

# Single user for simple testing
GET_GITLAB_ORG_MEMBERS = [
    {
        "id": 1,
        "username": "alice",
        "name": "Alice Smith",
        "state": "active",
        "email": None,
        "web_url": "https://gitlab.example.com/alice",
        "is_admin": False,
        "access_level": 50,
    },
]

# User is member of the Platform group
GET_GITLAB_GROUP_MEMBERS = [
    {
        "id": 1,
        "username": "alice",
        "name": "Alice Smith",
        "state": "active",
        "email": None,
        "web_url": "https://gitlab.example.com/alice",
        "is_admin": False,
        "access_level": 40,  # Maintainer
    },
]

# User committed to the project
GET_GITLAB_COMMITS = [
    {
        "id": "a1b2c3d4e5f6",
        "author_name": "Alice Smith",
        "author_email": "alice@example.com",
        "committed_date": "2024-12-01T10:00:00Z",
        "message": "Initial commit",
    },
    {
        "id": "b2c3d4e5f6a7",
        "author_name": "Alice Smith",
        "author_email": "alice@example.com",
        "committed_date": "2024-12-05T14:30:00Z",
        "message": "Update code",
    },
]
