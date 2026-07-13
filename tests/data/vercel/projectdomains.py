# Raw data shape returned by GET /v9/projects/{projectId}/domains.
# These records upsert minimal VercelDomain nodes and create
# VercelProject-[:HAS_DOMAIN]->VercelDomain relationships with per-project props.
VERCEL_PROJECT_DOMAINS = [
    {
        "name": "example.com",
        "redirect": None,
        "redirectStatusCode": None,
        "gitBranch": None,
        "verified": True,
        "createdAt": 1640995200000,
        "updatedAt": 1640995260000,
    },
    {
        "name": "www.example.com",
        "redirect": "example.com",
        "redirectStatusCode": 308,
        "gitBranch": None,
        "verified": True,
        "createdAt": 1640995300000,
        "updatedAt": 1640995360000,
    },
]
