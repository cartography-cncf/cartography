from tests.data.langsmith.organizations import LANGSMITH_ORG_ID

ORG_ADMIN_ROLE_ID = "11111111-1111-4111-8111-111111111111"
WORKSPACE_VIEWER_ROLE_ID = "22222222-2222-4222-8222-222222222222"
CUSTOM_ROLE_ID = "33333333-3333-4333-8333-333333333333"

LANGSMITH_ROLES = [
    {
        "id": ORG_ADMIN_ROLE_ID,
        # Built-in roles carry no organization_id.
        "name": "ORGANIZATION_ADMIN",
        "display_name": "Organization Admin",
        "description": "Full access to the organization.",
        "organization_id": None,
        "access_scope": "organization",
        "is_restricted": False,
        "permissions": ["organization:manage", "organization:read"],
    },
    {
        "id": WORKSPACE_VIEWER_ROLE_ID,
        "name": "WORKSPACE_VIEWER",
        "display_name": "Viewer",
        "description": "Read-only access to a workspace.",
        "organization_id": None,
        "access_scope": "workspace",
        "is_restricted": False,
        "permissions": ["workspaces:read"],
    },
    {
        # Every organization-defined role is stored under the system name CUSTOM, so only
        # display_name and id distinguish them.
        "id": CUSTOM_ROLE_ID,
        "name": "CUSTOM",
        "display_name": "Deployment Auditor",
        "description": "Can read deployments and their agent credentials.",
        "organization_id": LANGSMITH_ORG_ID,
        "access_scope": "workspace",
        "is_restricted": True,
        "permissions": ["workspaces:read", "deployments:read"],
    },
]
