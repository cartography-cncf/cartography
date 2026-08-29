# Raw shape of GET /project/{project-slug}, keyed by slug.
CIRCLECI_PROJECTS = {
    "gh/acme/web": {
        "id": "proj-1",
        "slug": "gh/acme/web",
        "name": "web",
        "organization_name": "Acme Corp",
        "organization_slug": "gh/acme",
        "organization_id": "org-1111-aaaa",
        "vcs_info": {
            "vcs_url": "https://github.com/acme/web",
            "provider": "GitHub",
            "default_branch": "main",
        },
    },
    "gh/acme/api": {
        "id": "proj-2",
        "slug": "gh/acme/api",
        "name": "api",
        "organization_name": "Acme Corp",
        "organization_slug": "gh/acme",
        "organization_id": "org-1111-aaaa",
        "vcs_info": {
            "vcs_url": "https://github.com/acme/api",
            "provider": "GitHub",
            "default_branch": "main",
        },
    },
}
