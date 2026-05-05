"""Test data for GitLab environments module."""

TEST_GITLAB_URL = "https://gitlab.example.com"
TEST_PROJECT_ID = 123

# Raw response from /api/v4/projects/:id/environments
GET_ENVIRONMENTS_RESPONSE = [
    {
        "id": 1,
        "name": "production",
        "slug": "production",
        "external_url": "https://prod.example.com",
        "state": "available",
        "tier": "production",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-04-01T00:00:00Z",
        "auto_stop_at": None,
    },
    {
        "id": 2,
        "name": "staging",
        "slug": "staging",
        "external_url": "https://staging.example.com",
        "state": "available",
        "tier": "staging",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-04-01T00:00:00Z",
        "auto_stop_at": None,
    },
    {
        "id": 3,
        "name": "review/feature-x",
        "slug": "review-feature-x",
        "external_url": None,
        "state": "stopped",
        "tier": "development",
        "created_at": "2026-04-15T00:00:00Z",
        "updated_at": "2026-04-29T00:00:00Z",
        "auto_stop_at": None,
    },
]
