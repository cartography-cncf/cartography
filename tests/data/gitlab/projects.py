"""Test data for GitLab projects module."""

import json

# Raw GitLab API response format - matches what /groups/:id/projects returns
GET_GITLAB_PROJECTS_RESPONSE = [
    {
        "id": 123,
        "name": "awesome-project",
        "path": "awesome-project",
        "path_with_namespace": "myorg/awesome-project",
        "web_url": "https://gitlab.example.com/myorg/awesome-project",
        "description": "An awesome project for testing",
        "visibility": "private",
        "archived": False,
        "default_branch": "main",
        "created_at": "2024-01-15T10:30:00Z",
        "last_activity_at": "2024-12-15T14:45:00Z",
        "namespace": {
            "id": 10,
            "name": "MyOrg",
            "path": "myorg",
            "kind": "group",
            "full_path": "myorg",
            "web_url": "https://gitlab.example.com/myorg",
        },
    },
    {
        "id": 456,
        "name": "backend-service",
        "path": "backend-service",
        "path_with_namespace": "myorg/platform/backend-service",
        "web_url": "https://gitlab.example.com/myorg/platform/backend-service",
        "description": "Backend microservice",
        "visibility": "internal",
        "archived": False,
        "default_branch": "master",
        "created_at": "2024-03-20T08:15:00Z",
        "last_activity_at": "2024-12-18T16:20:00Z",
        "namespace": {
            "id": 20,
            "name": "Platform",
            "path": "platform",
            "kind": "group",
            "full_path": "myorg/platform",
            "web_url": "https://gitlab.example.com/myorg/platform",
        },
    },
    {
        "id": 789,
        "name": "frontend-app",
        "path": "frontend-app",
        "path_with_namespace": "myorg/apps/frontend-app",
        "web_url": "https://gitlab.example.com/myorg/apps/frontend-app",
        "description": "Frontend application",
        "visibility": "public",
        "archived": False,
        "default_branch": "main",
        "created_at": "2024-05-10T12:00:00Z",
        "last_activity_at": "2024-12-19T09:30:00Z",
        "namespace": {
            "id": 30,
            "name": "Apps",
            "path": "apps",
            "kind": "group",
            "full_path": "myorg/apps",
            "web_url": "https://gitlab.example.com/myorg/apps",
        },
    },
]

# Languages by project ID - matches what _fetch_all_languages returns
LANGUAGES_BY_PROJECT = {
    123: {"Python": 65.5, "JavaScript": 34.5},
    456: {"Go": 85.0, "Shell": 15.0},
    789: {"TypeScript": 70.0, "CSS": 25.0, "HTML": 5.0},
}

# Expected transformed projects output (with languages as JSON strings)
TRANSFORMED_PROJECTS = [
    {
        "web_url": "https://gitlab.example.com/myorg/awesome-project",
        "name": "awesome-project",
        "path": "awesome-project",
        "path_with_namespace": "myorg/awesome-project",
        "description": "An awesome project for testing",
        "visibility": "private",
        "default_branch": "main",
        "archived": False,
        "created_at": "2024-01-15T10:30:00Z",
        "last_activity_at": "2024-12-15T14:45:00Z",
        "org_url": "https://gitlab.example.com/myorg",
        "group_url": None,  # Org-level project
        "languages": json.dumps({"Python": 65.5, "JavaScript": 34.5}),
    },
    {
        "web_url": "https://gitlab.example.com/myorg/platform/backend-service",
        "name": "backend-service",
        "path": "backend-service",
        "path_with_namespace": "myorg/platform/backend-service",
        "description": "Backend microservice",
        "visibility": "internal",
        "default_branch": "master",
        "archived": False,
        "created_at": "2024-03-20T08:15:00Z",
        "last_activity_at": "2024-12-18T16:20:00Z",
        "org_url": "https://gitlab.example.com/myorg",
        "group_url": "https://gitlab.example.com/myorg/platform",  # Nested group
        "languages": json.dumps({"Go": 85.0, "Shell": 15.0}),
    },
    {
        "web_url": "https://gitlab.example.com/myorg/apps/frontend-app",
        "name": "frontend-app",
        "path": "frontend-app",
        "path_with_namespace": "myorg/apps/frontend-app",
        "description": "Frontend application",
        "visibility": "public",
        "default_branch": "main",
        "archived": False,
        "created_at": "2024-05-10T12:00:00Z",
        "last_activity_at": "2024-12-19T09:30:00Z",
        "org_url": "https://gitlab.example.com/myorg",
        "group_url": "https://gitlab.example.com/myorg/apps",  # Nested group
        "languages": json.dumps({"TypeScript": 70.0, "CSS": 25.0, "HTML": 5.0}),
    },
]
