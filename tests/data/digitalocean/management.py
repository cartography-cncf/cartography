from typing import Any

PROJECTS_RESPONSE: dict[str, Any] = {
    "projects": [
        {
            "id": "test-project-uuid",
            "owner_uuid": "test-owner-uuid",
            "owner_id": 11223344,
            "name": "project_1",
            "description": "Update your project information under Settings",
            "purpose": "",
            "environment": "",
            "is_default": True,
            "created_at": "2026-02-18T01:44:47Z",
            "updated_at": "2026-02-18T01:44:47Z",
        }
    ],
    "links": {
        "pages": {
            "first": "https://api.digitalocean.com/v2/projects?page=1&per_page=20",
            "last": "https://api.digitalocean.com/v2/projects?page=1&per_page=20",
        }
    },
    "meta": {"total": 2},
}

PROJECTS_RESPONSE_PAGINATED: list[dict[str, Any]] = [
    {
        "projects": [
            {
                "id": "test-project-uuid",
                "owner_uuid": "test-owner-uuid",
                "name": "project_1",
            }
        ],
        "links": {
            "pages": {
                "first": "https://api.digitalocean.com/v2/projects?page=1&per_page=20",
                "next": "https://api.digitalocean.com/v2/projects?page=2&per_page=20",
                "last": "https://api.digitalocean.com/v2/projects?page=2&per_page=20",
            }
        },
        "meta": {"total": 2},
    },
    {
        "projects": [
            {
                "id": "test-project-uuid-2",
                "owner_uuid": "test-owner-uuid-2",
                "name": "project_2",
            }
        ],
        "links": {
            "pages": {
                "first": "https://api.digitalocean.com/v2/projects?page=1&per_page=20",
                "last": "https://api.digitalocean.com/v2/projects?page=1&per_page=20",
            }
        },
        "meta": {"total": 2},
    },
]

PROJECT_RESOURCES_RESPONSE: dict[str, Any] = {
    "resources": [
        {
            "urn": "do:droplet:568030246",
            "assigned_at": "2026-04-29T19:04:22.167913Z",
            "links": {"self": "https://api.digitalocean.com/v2/droplets/568030246"},
            "status": "ok",
        }
    ]
}
