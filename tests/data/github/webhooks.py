ORG_WEBHOOKS = [
    {
        "id": 501,
        "url": "https://api.github.com/orgs/simpsoncorp/hooks/501",
        "ping_url": "https://api.github.com/orgs/simpsoncorp/hooks/501/pings",
        "deliveries_url": "https://api.github.com/orgs/simpsoncorp/hooks/501/deliveries",
        "name": "web",
        "events": ["*"],
        "active": True,
        "config": {
            "url": "https://siem.simpsoncorp.example/github?token=abc123",
            "content_type": "json",
            "insecure_ssl": "0",
            "secret": "********",
        },
        "created_at": "2024-01-02T03:04:05Z",
        "updated_at": "2024-01-02T03:04:05Z",
        "type": "Organization",
    },
]

REPO_WEBHOOKS = {
    "simpsoncorp/sample_repo": [
        {
            "type": "Repository",
            "id": 601,
            "name": "web",
            "active": True,
            "events": ["push", "pull_request"],
            "config": {
                "content_type": "form",
                "insecure_ssl": "1",
                "url": "http://jenkins.simpsoncorp.example:8080/github-webhook/",
            },
            "updated_at": "2024-02-02T03:04:05Z",
            "created_at": "2024-02-02T03:04:05Z",
            "url": "https://api.github.com/repos/simpsoncorp/sample_repo/hooks/601",
            "test_url": "https://api.github.com/repos/simpsoncorp/sample_repo/hooks/601/test",
            "ping_url": "https://api.github.com/repos/simpsoncorp/sample_repo/hooks/601/pings",
            "deliveries_url": "https://api.github.com/repos/simpsoncorp/sample_repo/hooks/601/deliveries",
            "last_response": {"code": 200, "status": "active", "message": "OK"},
        },
    ],
    "simpsoncorp/another_repo": [],
}
