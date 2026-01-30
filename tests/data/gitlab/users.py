"""Test data for GitLab users module."""

TEST_ORG_URL = "https://gitlab.example.com/myorg"

# Organization members: Alice and Bob are org-level members
# Alice has email available (will match by email), Bob doesn't (will match by name)
GET_GITLAB_ORG_MEMBERS = [
    {
        "id": 1,
        "username": "alice",
        "name": "Alice Smith",
        "state": "active",
        "email": "alice@example.com",  # Email available - will match by email
        "web_url": "https://gitlab.example.com/alice",
        "is_admin": False,
        "access_level": 50,  # Owner at org level
    },
    {
        "id": 2,
        "username": "bob",
        "name": "Bob Jones",
        "state": "active",
        "email": None,  # Email not available - will match by name fallback
        "web_url": "https://gitlab.example.com/bob",
        "is_admin": False,
        "access_level": 10,  # Guest at org level
    },
]

# Group members: Only Alice is in the Platform group
GET_GITLAB_GROUP_MEMBERS = [
    {
        "id": 1,
        "username": "alice",
        "name": "Alice Smith",
        "state": "active",
        "email": "alice@example.com",  # Email available - will match by email
        "web_url": "https://gitlab.example.com/alice",
        "is_admin": False,
        "access_level": 40,  # Maintainer in Platform group
    },
]

# Commits from both Alice and Bob
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
    {
        "id": "c3d4e5f6a7b8",
        "author_name": "Bob Jones",
        "author_email": "bob@example.com",
        "committed_date": "2024-12-03T09:15:00Z",
        "message": "Add feature",
    },
]
