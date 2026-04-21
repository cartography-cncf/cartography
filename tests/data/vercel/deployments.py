VERCEL_DEPLOYMENTS = [
    {
        "uid": "dpl_123",
        "name": "acme-web",
        "url": "acme-web-abc123.vercel.app",
        "created": 1640995200000,
        "ready": 1640995260000,
        "state": "READY",
        "target": "production",
        "source": "git",
        "creator": {
            "uid": "user_homer",
        },
        "meta": {
            "githubCommitSha": "abcdef1234567890",
            "branchAlias": "acme-web-main.vercel.app",
        },
    },
    {
        "uid": "dpl_456",
        "name": "acme-docs",
        "url": "acme-docs-def456.vercel.app",
        "created": 1641000000000,
        "ready": 1641000120000,
        "state": "BUILDING",
        "target": "preview",
        "source": "cli",
        "creator": {
            "uid": "user_homer",
        },
        "meta": {
            "githubCommitSha": "1234567890abcdef",
            "branchAlias": "acme-docs-feature.vercel.app",
        },
    },
]
