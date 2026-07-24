"""Test fixtures for the Doppler intel module.

Each constant is shaped like the corresponding `get()` return value so tests can
patch `get` and exercise transform + load. Secret fixtures contain NAMES only,
mirroring the module's hard rule against ingesting secret values.
"""

WORKPLACE = {
    "id": "wp1",
    "name": "Acme",
    "billing_email": "billing@acme.io",
    "security_email": "security@acme.io",
}

# get() returns (workplace_roles, project_roles)
WORKPLACE_ROLES = [
    {
        "identifier": "admin",
        "name": "Admin",
        "permissions": ["workplace_admin"],
        "is_custom_role": False,
        "is_inline_role": False,
        "created_at": "2024-01-01T00:00:00Z",
    },
]
PROJECT_ROLES = [
    {
        "identifier": "collaborator",
        "name": "Collaborator",
        "permissions": ["project_config_logs"],
        "is_custom_role": False,
        "created_at": "2024-01-01T00:00:00Z",
    },
]

# Raw /workplace/users shape (nested user object); transform() flattens it.
USERS = [
    {
        "id": "u1",
        "access": "owner",
        "created_at": "2024-01-02T00:00:00Z",
        "user": {
            "email": "alice@acme.io",
            "name": "Alice",
            "username": "alice",
            "profile_image_url": "https://img/alice",
        },
    },
]

# get() returns (groups_raw, memberships)
GROUPS = [
    {
        "slug": "g1",
        "name": "Engineering",
        "created_at": "2024-01-03T00:00:00Z",
        "default_project_role": {"identifier": "collaborator"},
    },
]
GROUP_MEMBERSHIPS = [{"user_id": "u1", "group_slug": "g1"}]

# get() returns (accounts_raw, tokens, identities)
SERVICE_ACCOUNTS = [
    {
        "slug": "sa1",
        "name": "ci-bot",
        "created_at": "2024-01-04T00:00:00Z",
        "workplace_role": {"identifier": "admin"},
    },
]
SERVICE_ACCOUNT_TOKENS = [
    {
        "slug": "sat1",
        "name": "deploy-token",
        "created_at": "2024-01-05T00:00:00Z",
        "expires_at": None,
        "last_seen_at": "2024-02-01T00:00:00Z",
        "service_account_slug": "sa1",
    },
]
SERVICE_ACCOUNT_IDENTITIES = [
    {
        "slug": "sai1",
        "name": "github-oidc",
        "method": "oidc",
        "ttl_seconds": 3600,
        "created_at": "2024-01-06T00:00:00Z",
        "last_seen_at": "2024-02-02T00:00:00Z",
        "service_account_slug": "sa1",
    },
]

PROJECTS = [
    {
        "id": "p1",
        "slug": "backend",
        "name": "Backend",
        "description": "Backend services",
        "created_at": "2024-01-07T00:00:00Z",
    },
]

# environments.get() output (composite ids already built)
ENVIRONMENTS = [
    {
        "id": "backend/dev",
        "env_id": "dev",
        "name": "Development",
        "project": "backend",
        "created_at": "2024-01-08T00:00:00Z",
        "initial_fetch_at": None,
    },
]

# configs.get() output (full config dicts with composite ids)
CONFIGS = [
    {
        "name": "dev",
        "project": "backend",
        "environment": "dev",
        "root": True,
        "locked": False,
        "created_at": "2024-01-09T00:00:00Z",
        "id": "backend/dev",
        "environment_id": "backend/dev",
    },
]
# configs.sync() return value (refs reused by per-config fan-out)
CONFIG_REFS = [{"project": "backend", "config": "dev", "config_id": "backend/dev"}]

# Secret NAMES only.
SECRETS = [
    {
        "id": "backend/dev/DATABASE_URL",
        "name": "DATABASE_URL",
        "project": "backend",
        "config": "dev",
        "config_id": "backend/dev",
    },
]

SERVICE_TOKENS = [
    {
        "slug": "st1",
        "name": "lambda-token",
        "project": "backend",
        "environment": "dev",
        "config": "dev",
        "created_at": "2024-01-10T00:00:00Z",
        "expires_at": None,
        "config_id": "backend/dev",
    },
]

TRUSTED_IPS = [
    {"id": "backend/dev/10.0.0.0/8", "cidr": "10.0.0.0/8", "config_id": "backend/dev"},
]

# Raw /integrations shape with embedded syncs; transform() lifts the syncs out.
INTEGRATIONS = [
    {
        "slug": "int1",
        "name": "AWS Secrets Manager",
        "type": "aws_secrets_manager",
        "kind": "sync",
        "enabled": True,
        "syncs": [
            {
                "slug": "sync1",
                "enabled": True,
                "lastSyncedAt": "2024-02-03T00:00:00Z",
                "project": "backend",
                "config": "dev",
                "integration": "int1",
            },
        ],
    },
]

WEBHOOKS = [
    {
        "id": "wh1",
        "name": "Slack notifier",
        "url": "https://hooks.slack.com/services/xxx",
        "enabled": True,
        "project": "backend",
    },
]

# members.get() output: member records grouped by type.
PROJECT_MEMBERS = {
    "workplace_user": [
        {
            "slug": "u1",
            "project": "backend",
            "role": "collaborator",
            "access_all_environments": True,
        },
    ],
    "group": [
        {
            "slug": "g1",
            "project": "backend",
            "role": "viewer",
            "access_all_environments": False,
        },
    ],
    "service_account": [
        {
            "slug": "sa1",
            "project": "backend",
            "role": "admin",
            "access_all_environments": True,
        },
    ],
}
