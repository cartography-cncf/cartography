API_URL = "https://app.infisical.example"
ORGANIZATION_ID = "org-123"

PROJECTS = [
    {
        "id": "project-1",
        "name": "Payments",
        "slug": "payments",
        "organization": ORGANIZATION_ID,
        "environments": [
            {"name": "Development", "slug": "dev"},
            {"name": "Production", "slug": "prod"},
        ],
    },
    {
        "id": "project-2",
        "name": "Data Platform",
        "slug": "data-platform",
        "organization": ORGANIZATION_ID,
        "environments": [{"name": "Production", "slug": "prod"}],
    },
]
