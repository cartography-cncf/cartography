"""
Test data for GitHub Actions (workflows, secrets, variables, environments).
"""

# Organization-level secrets
GET_ORG_SECRETS = [
    {
        "name": "NPM_TOKEN",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-06-01T12:00:00Z",
        "visibility": "all",
    },
    {
        "name": "AWS_ACCESS_KEY_ID",
        "created_at": "2024-02-20T08:30:00Z",
        "updated_at": "2024-02-20T08:30:00Z",
        "visibility": "private",
    },
]

# Organization-level variables
GET_ORG_VARIABLES = [
    {
        "name": "NODE_VERSION",
        "value": "18",
        "created_at": "2024-01-10T09:00:00Z",
        "updated_at": "2024-03-15T14:00:00Z",
        "visibility": "all",
    },
    {
        "name": "DEPLOY_ENV",
        "value": "production",
        "created_at": "2024-01-10T09:00:00Z",
        "updated_at": "2024-01-10T09:00:00Z",
        "visibility": "selected",
    },
]

# Repository workflows
GET_REPO_WORKFLOWS = [
    {
        "id": 12345678,
        "name": "CI",
        "path": ".github/workflows/ci.yml",
        "state": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-06-15T10:30:00Z",
        "html_url": "https://github.com/simpsoncorp/sample_repo/blob/main/.github/workflows/ci.yml",
    },
    {
        "id": 12345679,
        "name": "Deploy",
        "path": ".github/workflows/deploy.yml",
        "state": "active",
        "created_at": "2024-02-01T00:00:00Z",
        "updated_at": "2024-05-20T16:45:00Z",
        "html_url": "https://github.com/simpsoncorp/sample_repo/blob/main/.github/workflows/deploy.yml",
    },
    {
        "id": 12345680,
        "name": "Stale Check",
        "path": ".github/workflows/stale.yml",
        "state": "disabled_manually",
        "created_at": "2024-03-01T00:00:00Z",
        "updated_at": "2024-04-10T11:00:00Z",
        "html_url": "https://github.com/simpsoncorp/sample_repo/blob/main/.github/workflows/stale.yml",
    },
]

# Repository environments
GET_REPO_ENVIRONMENTS = [
    {
        "id": 987654321,
        "name": "production",
        "html_url": "https://github.com/simpsoncorp/sample_repo/settings/environments/987654321",
        "created_at": "2024-01-05T00:00:00Z",
        "updated_at": "2024-06-01T00:00:00Z",
    },
    {
        "id": 987654322,
        "name": "staging",
        "html_url": "https://github.com/simpsoncorp/sample_repo/settings/environments/987654322",
        "created_at": "2024-01-05T00:00:00Z",
        "updated_at": "2024-05-15T00:00:00Z",
    },
]

# Repository-level secrets
GET_REPO_SECRETS = [
    {
        "name": "DEPLOY_KEY",
        "created_at": "2024-01-20T10:00:00Z",
        "updated_at": "2024-04-01T12:00:00Z",
    },
    {
        "name": "DATABASE_URL",
        "created_at": "2024-02-15T08:30:00Z",
        "updated_at": "2024-02-15T08:30:00Z",
    },
]

# Repository-level variables
GET_REPO_VARIABLES = [
    {
        "name": "LOG_LEVEL",
        "value": "info",
        "created_at": "2024-01-10T09:00:00Z",
        "updated_at": "2024-03-01T14:00:00Z",
    },
    {
        "name": "MAX_RETRIES",
        "value": "3",
        "created_at": "2024-01-10T09:00:00Z",
        "updated_at": "2024-01-10T09:00:00Z",
    },
]

# Environment-level secrets (for 'production' environment)
GET_ENV_SECRETS_PRODUCTION = [
    {
        "name": "PROD_API_KEY",
        "created_at": "2024-01-25T10:00:00Z",
        "updated_at": "2024-05-01T12:00:00Z",
    },
]

# Environment-level variables (for 'production' environment)
GET_ENV_VARIABLES_PRODUCTION = [
    {
        "name": "API_URL",
        "value": "https://api.production.example.com",
        "created_at": "2024-01-25T10:00:00Z",
        "updated_at": "2024-01-25T10:00:00Z",
    },
]

# Environment-level secrets (for 'staging' environment)
GET_ENV_SECRETS_STAGING = [
    {
        "name": "STAGING_API_KEY",
        "created_at": "2024-01-25T10:00:00Z",
        "updated_at": "2024-03-01T12:00:00Z",
    },
]

# Environment-level variables (for 'staging' environment)
GET_ENV_VARIABLES_STAGING = [
    {
        "name": "API_URL",
        "value": "https://api.staging.example.com",
        "created_at": "2024-01-25T10:00:00Z",
        "updated_at": "2024-02-15T10:00:00Z",
    },
    {
        "name": "DEBUG_MODE",
        "value": "true",
        "created_at": "2024-02-01T10:00:00Z",
        "updated_at": "2024-02-01T10:00:00Z",
    },
]
