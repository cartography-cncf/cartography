# Raw items of GET /projects/{project_id}/pipeline-definitions (a pipeline is
# the config/source binding; runs are intentionally not ingested).
CIRCLECI_PIPELINES = [
    {
        "id": "def-1",
        "name": "build-and-test",
        "description": "Default pipeline",
        "created_at": "2021-09-01T09:00:00Z",
        "config_source": {
            "provider": "github_app",
            "repo": {"full_name": "acme/web", "external_id": "123456"},
            "file_path": ".circleci/config.yml",
        },
        "checkout_source": {
            "provider": "github_app",
            "repo": {"full_name": "acme/web", "external_id": "123456"},
        },
    },
]
