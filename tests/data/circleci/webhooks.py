# Raw items of GET /webhook?scope-id=...&scope-type=project.
CIRCLECI_WEBHOOKS = [
    {
        "id": "wh-1",
        "name": "deploy-notify",
        "url": "https://hooks.example.com/circleci",
        "verify-tls": True,
        "signing-secret": "****",
        "events": ["workflow-completed", "job-completed"],
        "scope": {"id": "proj-1", "type": "project"},
    },
]
