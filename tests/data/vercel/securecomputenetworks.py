# Raw /v1/connect/networks response. The project list here is flat (just IDs);
# per-environment and passive/active details live in each project's
# `connectConfigurations` (see VERCEL_PROJECTS_WITH_CONNECT_CONFIG below).
VERCEL_RAW_NETWORKS = [
    {
        "id": "scn_123",
        "name": "prod-network",
        "region": "iad1",
        "status": "ready",
        "createdAt": 1640995200000,
        "projects": {"count": 1, "ids": ["prj_abc"]},
    },
    {
        "id": "scn_456",
        "name": "staging-network",
        "region": "sfo1",
        "status": "ready",
        "createdAt": 1641081600000,
        "projects": {"count": 1, "ids": ["prj_abc"]},
    },
]

# A project entry from /v9/projects carrying `connectConfigurations` that
# reference both test networks. prj_abc is attached to scn_123 in production
# (active) + preview (passive), and to scn_456 in development (active).
VERCEL_PROJECTS_WITH_CONNECT_CONFIG = [
    {
        "id": "prj_abc",
        "name": "test-project",
        "connectConfigurations": [
            {
                "connectConfigurationId": "scn_123",
                "envId": "production",
                "passive": False,
                "buildsEnabled": True,
            },
            {
                "connectConfigurationId": "scn_123",
                "envId": "preview",
                "passive": True,
                "buildsEnabled": False,
            },
            {
                "connectConfigurationId": "scn_456",
                "envId": "development",
                "passive": False,
                "buildsEnabled": True,
            },
        ],
    },
]


# Node-shape data used by _ensure_local_neo4j_has_test_networks.
VERCEL_SECURE_COMPUTE_NETWORKS = [
    {
        "id": "scn_123",
        "name": "prod-network",
        "region": "iad1",
        "status": "ready",
        "createdAt": 1640995200000,
    },
    {
        "id": "scn_456",
        "name": "staging-network",
        "region": "sfo1",
        "status": "ready",
        "createdAt": 1641081600000,
    },
]
