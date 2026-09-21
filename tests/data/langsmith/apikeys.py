from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.roles import ORG_ADMIN_ROLE_ID
from tests.data.langsmith.users import BART_LS_USER_ID
from tests.data.langsmith.users import MARGE_ORG_IDENTITY_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID

LANGSMITH_SERVICE_ACCOUNTS = [
    {
        "id": "5a5a5a5a-0001-4001-8001-5a5a5a5a5a5a",
        "created_at": "2026-01-20T09:00:00Z",
        "updated_at": "2026-01-20T09:00:00Z",
        "name": "ci-deployer",
        "organization_id": LANGSMITH_ORG_ID,
        "default_workspace_id": WORKSPACE_PROD_ID,
    },
]

LANGSMITH_SERVICE_KEYS = [
    {
        "id": "6a6a6a6a-0001-4001-8001-6a6a6a6a6a6a",
        "short_key": "lsv2_sk_abcd",
        "description": "CI deploy key",
        "read_only": False,
        "created_at": "2026-01-20T09:00:00Z",
        "last_used_at": "2026-03-01T09:00:00Z",
        "expires_at": "2026-12-31T00:00:00Z",
        "revoked_at": None,
        "workspace_names": ["Production"],
        "default_workspace_name": "Production",
        "role_id": CUSTOM_ROLE_ID,
        "org_role_id": None,
        "access_scope": "workspace",
        "created_by": MARGE_ORG_IDENTITY_ID,
    },
]

LANGSMITH_PATS = [
    {
        # Owner is deactivated but the token was never revoked.
        "id": "7a7a7a7a-0001-4001-8001-7a7a7a7a7a7a",
        "short_key": "lsv2_pt_wxyz",
        "description": "Bart's laptop",
        "read_only": False,
        "created_at": "2026-01-25T09:00:00Z",
        "last_used_at": "2026-02-28T09:00:00Z",
        "expires_at": None,
        "revoked_at": None,
        "workspace_names": [],
        "default_workspace_name": None,
        "role_id": None,
        "org_role_id": ORG_ADMIN_ROLE_ID,
        "access_scope": "organization",
        "created_by": BART_LS_USER_ID,
    },
]

LANGSMITH_SCIM_TOKENS = [
    {
        "id": "8a8a8a8a-0001-4001-8001-8a8a8a8a8a8a",
        # SCIM tokens report their prefix as short_token rather than short_key.
        "short_token": "lsv2_sc_1234",
        "description": "Okta provisioning",
        "created_at": "2026-01-02T09:00:00Z",
        "created_by": MARGE_ORG_IDENTITY_ID,
        "last_used_at": "2026-03-03T09:00:00Z",
        "updated_at": "2026-01-02T09:00:00Z",
    },
]
