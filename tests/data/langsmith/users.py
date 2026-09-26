from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.roles import ORG_ADMIN_ROLE_ID
from tests.data.langsmith.roles import WORKSPACE_VIEWER_ROLE_ID
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID

HOMER_LS_USER_ID = "c1c1c1c1-0001-4001-8001-c1c1c1c1c1c1"
MARGE_LS_USER_ID = "c2c2c2c2-0002-4002-8002-c2c2c2c2c2c2"
BART_LS_USER_ID = "c3c3c3c3-0003-4003-8003-c3c3c3c3c3c3"

HOMER_ORG_IDENTITY_ID = "d1d1d1d1-0001-4001-8001-d1d1d1d1d1d1"
MARGE_ORG_IDENTITY_ID = "d2d2d2d2-0002-4002-8002-d2d2d2d2d2d2"
BART_ORG_IDENTITY_ID = "d3d3d3d3-0003-4003-8003-d3d3d3d3d3d3"

LANGSMITH_ACTIVE_ORG_MEMBERS = [
    {
        "id": MARGE_ORG_IDENTITY_ID,
        "organization_id": LANGSMITH_ORG_ID,
        "created_at": "2026-01-04T10:00:00Z",
        "user_id": "99999999-0002-4002-8002-999999999999",
        "ls_user_id": MARGE_LS_USER_ID,
        "read_only": False,
        "email": "mbsimpson@simpson.corp",
        "full_name": "Marge Simpson",
        "display_name": "Marge Simpson",
        "avatar_url": "https://simpson.corp/avatars/marge.png",
        "is_disabled": False,
        "org_role_id": ORG_ADMIN_ROLE_ID,
        "org_role_name": "Organization Admin",
        "tenant_ids": [WORKSPACE_PROD_ID, WORKSPACE_DEV_ID],
        "linked_login_methods": [
            {
                "provider": "oidc",
                "provisioning_method": "scim",
                "username": "mbsimpson",
            },
        ],
    },
    {
        "id": HOMER_ORG_IDENTITY_ID,
        "organization_id": LANGSMITH_ORG_ID,
        "created_at": "2026-01-06T10:00:00Z",
        "user_id": "99999999-0001-4001-8001-999999999999",
        "ls_user_id": HOMER_LS_USER_ID,
        "read_only": False,
        "email": "hjsimpson@simpson.corp",
        "full_name": "Homer Simpson",
        "display_name": "Homer Simpson",
        "avatar_url": "https://simpson.corp/avatars/homer.png",
        "is_disabled": False,
        "org_role_id": None,
        "org_role_name": "Organization User",
        "tenant_ids": [WORKSPACE_PROD_ID],
        "linked_login_methods": [
            {"provider": "email", "username": "hjsimpson"},
        ],
    },
    {
        # Deactivated by SCIM, but still owns a live personal access token and still has an
        # agent acting on their behalf.
        "id": BART_ORG_IDENTITY_ID,
        "organization_id": LANGSMITH_ORG_ID,
        "created_at": "2026-01-07T10:00:00Z",
        "user_id": "99999999-0003-4003-8003-999999999999",
        "ls_user_id": BART_LS_USER_ID,
        "read_only": False,
        "email": "bjsimpson@simpson.corp",
        "full_name": "Bart Simpson",
        "display_name": "Bart Simpson",
        "avatar_url": None,
        "is_disabled": True,
        "org_role_id": None,
        "org_role_name": "Organization User",
        "tenant_ids": [WORKSPACE_DEV_ID],
        "linked_login_methods": [
            {
                "provider": "oidc",
                "provisioning_method": "scim",
                "username": "bjsimpson",
            },
        ],
    },
]

# A pending invite has no ls_user_id until it is accepted, so it must not become a user node.
LANGSMITH_PENDING_ORG_MEMBERS: list[dict] = [
    {
        "id": "e1e1e1e1-0009-4009-8009-e1e1e1e1e1e1",
        "email": "lmsimpson@simpson.corp",
        "ls_user_id": None,
        "org_role_id": None,
        "org_role_name": "Organization User",
        "tenant_ids": [],
    },
]

LANGSMITH_WORKSPACE_MEMBERS = {
    WORKSPACE_PROD_ID: {
        "tenant_id": WORKSPACE_PROD_ID,
        "members": [
            {
                "id": "f1f1f1f1-0001-4001-8001-f1f1f1f1f1f1",
                "ls_user_id": MARGE_LS_USER_ID,
                "email": "mbsimpson@simpson.corp",
                "role_id": CUSTOM_ROLE_ID,
                "role_name": "Deployment Auditor",
                "is_disabled": False,
                "created_at": "2026-01-04T10:00:00Z",
            },
            {
                "id": "f2f2f2f2-0002-4002-8002-f2f2f2f2f2f2",
                "ls_user_id": HOMER_LS_USER_ID,
                "email": "hjsimpson@simpson.corp",
                "role_id": WORKSPACE_VIEWER_ROLE_ID,
                "role_name": "Viewer",
                "is_disabled": False,
                "created_at": "2026-01-06T10:00:00Z",
            },
        ],
        "pending": [],
    },
    WORKSPACE_DEV_ID: {
        "tenant_id": WORKSPACE_DEV_ID,
        "members": [
            {
                "id": "f3f3f3f3-0003-4003-8003-f3f3f3f3f3f3",
                "ls_user_id": BART_LS_USER_ID,
                "email": "bjsimpson@simpson.corp",
                "role_id": CUSTOM_ROLE_ID,
                "role_name": "Deployment Auditor",
                "is_disabled": True,
                "created_at": "2026-01-07T10:00:00Z",
            },
        ],
        "pending": [],
    },
}
