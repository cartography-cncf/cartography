from tests.data.langsmith.deployments import SUPPORT_AGENT_ID
from tests.data.langsmith.deployments import TRIAGE_AGENT_ID
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.users import BART_LS_USER_ID
from tests.data.langsmith.users import HOMER_LS_USER_ID
from tests.data.langsmith.users import MARGE_LS_USER_ID

GITHUB_PROVIDER_ID = "p1p1p1p1-0001-4001-8001-p1p1p1p1p1p1"
GOOGLE_PROVIDER_ID = "p2p2p2p2-0002-4002-8002-p2p2p2p2p2p2"

# OAuth providers, returned per workspace but organization-scoped.
LANGSMITH_OAUTH_PROVIDERS = [
    {
        "id": GITHUB_PROVIDER_ID,
        "organization_id": LANGSMITH_ORG_ID,
        "provider_id": "github-prod",
        "name": "GitHub Production",
        "client_id": "Iv1.abcdef0123456789",
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "uses_pkce": True,
        "code_challenge_method": "S256",
        "provider_type": "oauth2",
        "mcp_server_url": None,
        "token_endpoint_auth_method": "client_secret_post",
        "is_dynamic_client": False,
        "allowed_redirect_uris": [
            "https://smith.langchain.com/host-oauth-callback/github-prod"
        ],
        "created_at": "2026-01-10T09:00:00Z",
        "updated_at": "2026-01-10T09:00:00Z",
    },
    {
        "id": GOOGLE_PROVIDER_ID,
        "organization_id": LANGSMITH_ORG_ID,
        "provider_id": "google-workspace",
        "name": "Google Workspace",
        "client_id": "1234567890-abcdef.apps.googleusercontent.com",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "uses_pkce": True,
        "provider_type": "oauth2",
        "mcp_server_url": None,
        "token_endpoint_auth_method": "client_secret_post",
        "is_dynamic_client": False,
        "allowed_redirect_uris": [],
        "created_at": "2026-01-11T09:00:00Z",
        "updated_at": "2026-01-11T09:00:00Z",
    },
]

# Keyed by agent: this is the organization-wide agent -> user token view.
LANGSMITH_AGENT_CONNECTIONS = {
    SUPPORT_AGENT_ID: {
        "data": [
            {
                "id": "cc11cc11-0001-4001-8001-cc11cc11cc11",
                "agent_id": SUPPORT_AGENT_ID,
                "oauth_token_id": "tok-1111",
                "provider_id": "github-prod",
                "provider_account_label": "marge-simpson",
                "scopes": ["repo", "read:org"],
                "expires_at": "2026-12-01T00:00:00Z",
                "created_by": MARGE_LS_USER_ID,
                "created_at": "2026-02-10T09:00:00Z",
            },
            {
                "id": "cc11cc11-0002-4002-8002-cc11cc11cc11",
                "agent_id": SUPPORT_AGENT_ID,
                "oauth_token_id": "tok-2222",
                "provider_id": "google-workspace",
                "provider_account_label": "hjsimpson@simpson.corp",
                "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
                "expires_at": None,
                "created_by": HOMER_LS_USER_ID,
                "created_at": "2026-02-11T09:00:00Z",
            },
        ],
    },
    TRIAGE_AGENT_ID: {
        "data": [
            {
                # Still live even though Bart's identity is deactivated.
                "id": "cc11cc11-0003-4003-8003-cc11cc11cc11",
                "agent_id": TRIAGE_AGENT_ID,
                "oauth_token_id": "tok-3333",
                "provider_id": "github-prod",
                "provider_account_label": "bart-simpson",
                "scopes": ["repo"],
                "expires_at": "2026-11-01T00:00:00Z",
                "created_by": BART_LS_USER_ID,
                "created_at": "2026-02-12T09:00:00Z",
            },
        ],
    },
}
