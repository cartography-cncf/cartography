"""
Sample GitHub Container Packages API responses for testing.
"""

# Sample response from GET /orgs/{org}/packages?package_type=container
GET_CONTAINER_PACKAGES = [
    {
        "id": 123456,
        "name": "my-app",
        "package_type": "container",
        "visibility": "public",
        "url": "https://api.github.com/orgs/test-org/packages/container/my-app",
        "html_url": "https://github.com/orgs/test-org/packages/container/my-app",
        "created_at": "2023-01-15T10:30:00Z",
        "updated_at": "2024-01-20T14:45:00Z",
        "owner": {
            "login": "test-org",
            "id": 789,
            "type": "Organization",
        },
        "repository": {
            "id": 456789,
            "name": "my-app-repo",
            "full_name": "test-org/my-app-repo",
        },
    },
    {
        "id": 123457,
        "name": "backend-service",
        "package_type": "container",
        "visibility": "private",
        "url": "https://api.github.com/orgs/test-org/packages/container/backend-service",
        "html_url": "https://github.com/orgs/test-org/packages/container/backend-service",
        "created_at": "2023-03-10T08:15:00Z",
        "updated_at": "2024-01-25T16:20:00Z",
        "owner": {
            "login": "test-org",
            "id": 789,
            "type": "Organization",
        },
        "repository": {
            "id": 456790,
            "name": "backend",
            "full_name": "test-org/backend",
        },
    },
    {
        "id": 123458,
        "name": "frontend-app",
        "package_type": "container",
        "visibility": "public",
        "url": "https://api.github.com/orgs/test-org/packages/container/frontend-app",
        "html_url": "https://github.com/orgs/test-org/packages/container/frontend-app",
        "created_at": "2023-06-20T12:00:00Z",
        "updated_at": "2024-01-28T09:30:00Z",
        "owner": {
            "login": "test-org",
            "id": 789,
            "type": "Organization",
        },
        "repository": None,  # Package not linked to a repository
    },
]


# Sample response from GET /orgs/{org}/packages/container/{package_name}/versions
GET_PACKAGE_VERSIONS = [
    {
        "id": 987654,
        "name": "sha256:abc123",
        "url": "https://api.github.com/orgs/test-org/packages/container/my-app/versions/987654",
        "package_html_url": "https://github.com/orgs/test-org/packages/container/my-app",
        "created_at": "2024-01-20T14:45:00Z",
        "updated_at": "2024-01-20T14:45:00Z",
        "html_url": "https://github.com/orgs/test-org/packages/container/my-app/987654",
        "metadata": {
            "package_type": "container",
            "container": {
                "tags": ["latest", "v1.2.3"],
            },
        },
    },
    {
        "id": 987655,
        "name": "sha256:def456",
        "url": "https://api.github.com/orgs/test-org/packages/container/my-app/versions/987655",
        "package_html_url": "https://github.com/orgs/test-org/packages/container/my-app",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "html_url": "https://github.com/orgs/test-org/packages/container/my-app/987655",
        "metadata": {
            "package_type": "container",
            "container": {
                "tags": ["v1.2.2"],
            },
        },
    },
]
