"""
Synthetic Airbyte account with three organizations, used to test how the module
behaves when the API denies access to one organization's users.

APP_OWNER is the user that owns the API application, so it belongs to every
organization. SHARED_USER belongs to both Alpha and Beta.
"""

API_URL = "https://airbyte.example.com/api/public/v1"

ORG_ALPHA = "0a0a0a0a-0000-4000-8000-00000000000a"
ORG_BETA = "0b0b0b0b-0000-4000-8000-00000000000b"
ORG_GAMMA = "0c0c0c0c-0000-4000-8000-00000000000c"

WS_ALPHA = "1a1a1a1a-0000-4000-8000-00000000001a"
WS_BETA = "1b1b1b1b-0000-4000-8000-00000000001b"
WS_GAMMA = "1c1c1c1c-0000-4000-8000-00000000001c"

SOURCE_ALPHA = "2a2a2a2a-0000-4000-8000-00000000002a"
SOURCE_BETA = "2b2b2b2b-0000-4000-8000-00000000002b"
SOURCE_GAMMA = "2c2c2c2c-0000-4000-8000-00000000002c"

APP_OWNER = "30000000-0000-4000-8000-000000000000"
SHARED_USER = "3a3b0000-0000-4000-8000-000000000000"
ALPHA_USER = "3a000000-0000-4000-8000-000000000000"
BETA_USER = "3b000000-0000-4000-8000-000000000000"
GAMMA_USER = "3c000000-0000-4000-8000-000000000000"
NEW_ALPHA_USER = "3a000000-0000-4000-8000-000000000001"

ORGANIZATIONS = [
    {
        "organizationId": ORG_ALPHA,
        "organizationName": "Alpha Data Co",
        "email": "ops@alpha.example.com",
    },
    {
        "organizationId": ORG_BETA,
        "organizationName": "Beta Analytics",
        "email": "ops@beta.example.com",
    },
    {
        "organizationId": ORG_GAMMA,
        "organizationName": "Gamma Labs",
        "email": "ops@gamma.example.com",
    },
]

# GET /workspaces takes no organizationId: it returns every workspace the
# application's user can read, whatever organization is being synced.
WORKSPACES = [
    {"workspaceId": WS_ALPHA, "name": "Alpha Warehouse", "dataResidency": "us"},
    {"workspaceId": WS_BETA, "name": "Beta Warehouse", "dataResidency": "eu"},
    {"workspaceId": WS_GAMMA, "name": "Gamma Warehouse", "dataResidency": "us"},
]

SOURCES = [
    {
        "sourceId": source_id,
        "name": f"Postgres {workspace_id[:2]}",
        "sourceType": "postgres",
        "definitionId": "decafbad-0000-4000-8000-000000000000",
        "workspaceId": workspace_id,
        "configuration": {"host": "db.example.com", "port": 5432},
    }
    for source_id, workspace_id in (
        (SOURCE_ALPHA, WS_ALPHA),
        (SOURCE_BETA, WS_BETA),
        (SOURCE_GAMMA, WS_GAMMA),
    )
]

USERS = {
    APP_OWNER: {"id": APP_OWNER, "name": "Sync Bot", "email": "bot@example.com"},
    SHARED_USER: {"id": SHARED_USER, "name": "Sam", "email": "sam@example.com"},
    ALPHA_USER: {"id": ALPHA_USER, "name": "Ada", "email": "ada@example.com"},
    BETA_USER: {"id": BETA_USER, "name": "Ben", "email": "ben@example.com"},
    GAMMA_USER: {"id": GAMMA_USER, "name": "Gia", "email": "gia@example.com"},
    NEW_ALPHA_USER: {"id": NEW_ALPHA_USER, "name": "Al", "email": "al@example.com"},
}


def permission(user_id: str, permission_type: str, scope: str, scope_id: str) -> dict:
    return {
        "permissionId": f"{user_id[:8]}-{scope_id[:8]}-{permission_type}",
        "permissionType": permission_type,
        "userId": user_id,
        "scope": scope,
        "scopeId": scope_id,
    }


def initial_permissions() -> dict[str, list[dict]]:
    """Permissions of each organization's users, keyed by organization id."""
    return {
        ORG_ALPHA: [
            permission(APP_OWNER, "organization_admin", "organization", ORG_ALPHA),
            permission(APP_OWNER, "workspace_reader", "workspace", WS_ALPHA),
            permission(ALPHA_USER, "organization_admin", "organization", ORG_ALPHA),
            permission(SHARED_USER, "organization_member", "organization", ORG_ALPHA),
        ],
        ORG_BETA: [
            permission(APP_OWNER, "organization_admin", "organization", ORG_BETA),
            permission(APP_OWNER, "workspace_admin", "workspace", WS_BETA),
            permission(SHARED_USER, "organization_admin", "organization", ORG_BETA),
            permission(BETA_USER, "organization_member", "organization", ORG_BETA),
        ],
        ORG_GAMMA: [
            permission(APP_OWNER, "organization_admin", "organization", ORG_GAMMA),
            permission(GAMMA_USER, "organization_member", "organization", ORG_GAMMA),
        ],
    }
