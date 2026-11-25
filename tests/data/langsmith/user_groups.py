from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.users import BART_ORG_IDENTITY_ID
from tests.data.langsmith.users import HOMER_ORG_IDENTITY_ID
from tests.data.langsmith.users import MARGE_ORG_IDENTITY_ID
from tests.data.langsmith.workspace_resources import ACCESS_POLICY_ID
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID

SUPPORT_GROUP_ID = "ca11ca11-0001-4001-8001-ca11ca11ca11"
# Granting Support into the production workspace created this workspace-scoped user group.
SUPPORT_PROD_GROUP_ID = "ca11ca11-0002-4002-8002-ca11ca11ca11"

LANGSMITH_USER_GROUPS = [
    {
        "id": SUPPORT_GROUP_ID,
        "organization_id": "unused",
        "name": "Support",
        "description": "Customer support engineers.",
        "idp_group_name": "okta-support",
        "idp_sync_enabled": True,
        "created_at": "2026-03-01T09:00:00Z",
        "updated_at": "2026-03-01T09:00:00Z",
    },
    {
        "id": SUPPORT_PROD_GROUP_ID,
        "organization_id": "unused",
        "workspace_id": WORKSPACE_PROD_ID,
        "parent_user_group_id": SUPPORT_GROUP_ID,
        "name": "Support",
        "description": "",
        "idp_sync_enabled": False,
        "created_at": "2026-03-01T09:00:00Z",
        "updated_at": "2026-03-01T09:00:00Z",
    },
]

# Listings are stored already unwrapped, the way the real client returns them.
LANGSMITH_USER_GROUP_MEMBERS = {
    SUPPORT_GROUP_ID: [
        {"identity_id": HOMER_ORG_IDENTITY_ID, "created_at": "2026-03-01T09:00:00Z"},
        {"identity_id": MARGE_ORG_IDENTITY_ID, "created_at": "2026-03-01T09:00:00Z"},
        # An identity that isn't an active member, such as one removed since.
        {
            "identity_id": "d9d9d9d9-0009-4009-8009-d9d9d9d9d9d9",
            "created_at": "2026-03-01T09:00:00Z",
        },
    ],
    SUPPORT_PROD_GROUP_ID: [
        {"identity_id": BART_ORG_IDENTITY_ID, "created_at": "2026-03-02T09:00:00Z"},
    ],
}

LANGSMITH_USER_GROUP_GRANTS = {
    SUPPORT_GROUP_ID: [
        {
            "workspace_id": WORKSPACE_PROD_ID,
            "role_id": CUSTOM_ROLE_ID,
            "role_name": "Deployment Auditor",
            "created_at": "2026-03-01T09:00:00Z",
            "updated_at": "2026-03-01T09:00:00Z",
        },
        {
            "workspace_id": WORKSPACE_DEV_ID,
            "role_id": CUSTOM_ROLE_ID,
            "role_name": "Deployment Auditor",
            "created_at": "2026-03-01T09:00:00Z",
            "updated_at": "2026-03-01T09:00:00Z",
        },
    ],
}

# The same policy is attached to Support for all its workspaces and, separately, for the
# production workspace only.
LANGSMITH_USER_GROUP_POLICIES = {
    SUPPORT_GROUP_ID: [
        {
            "id": ACCESS_POLICY_ID,
            "name": "Production projects only",
            "description": "",
            "effect": "allow",
            "attached_at": "2026-03-01T09:00:00Z",
        },
        {
            "id": ACCESS_POLICY_ID,
            "workspace_id": WORKSPACE_PROD_ID,
            "name": "Production projects only",
            "description": "",
            "effect": "allow",
            "attached_at": "2026-03-01T09:00:00Z",
        },
    ],
    SUPPORT_PROD_GROUP_ID: [],
}
