# Raw items of GET /projects/{project_id}/pipeline-definitions.
CIRCLECI_PIPELINE_DEFINITIONS = [
    {
        "id": "def-1",
        "name": "build-and-test",
        "description": "Default pipeline",
        "created_at": "2021-09-01T09:00:00Z",
        "config_source": {
            "provider": "github_app",
            "repo": "acme/web",
            "file_path": ".circleci/config.yml",
        },
        "checkout_source": {"provider": "github_app", "repo": "acme/web"},
    },
]
