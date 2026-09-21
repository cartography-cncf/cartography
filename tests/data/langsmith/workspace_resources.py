from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID

LANGSMITH_SSO_SETTINGS = [
    {
        "id": "9a9a9a9a-0001-4001-8001-9a9a9a9a9a9a",
        "organization_id": LANGSMITH_ORG_ID,
        "provider_id": "okta-saml",
        "default_workspace_role_id": CUSTOM_ROLE_ID,
        "default_workspace_ids": [WORKSPACE_PROD_ID, WORKSPACE_DEV_ID],
        "metadata_url": "https://simpson.okta.com/app/abc/sso/saml/metadata",
        "metadata_xml": "<EntityDescriptor>...</EntityDescriptor>",
        "sso_groups_enabled": True,
        "sso_groups_claim_field": "groups",
        "sso_groups_required": False,
        "sso_groups_role_sync_enabled": True,
        "attribute_mapping_load_error": None,
    },
]

LANGSMITH_ACCESS_POLICIES = {
    "access_policies": [
        {
            "id": "ab11ab11-0001-4001-8001-ab11ab11ab11",
            "name": "Production projects only",
            "description": "Restricts the auditor role to production-tagged projects.",
            "effect": "allow",
            "role_ids": [CUSTOM_ROLE_ID],
            "condition_groups": [
                {
                    "conditions": [
                        {
                            "attribute": "project.tag",
                            "operator": "in",
                            "value": ["prod"],
                        },
                    ],
                },
            ],
            "created_at": "2026-01-30T09:00:00Z",
            "updated_at": "2026-01-30T09:00:00Z",
        },
    ],
}

LANGSMITH_DATA_PLANES: list[dict] = []

LANGSMITH_SECRETS = {
    WORKSPACE_PROD_ID: [{"key": "OPENAI_API_KEY"}, {"key": "SLACK_BOT_TOKEN"}],
    WORKSPACE_DEV_ID: [{"key": "OPENAI_API_KEY"}],
}

LANGSMITH_TAG_KEYS = {
    WORKSPACE_PROD_ID: [
        {"id": "ac11ac11-0001-4001-8001-ac11ac11ac11", "key": "environment"},
    ],
    WORKSPACE_DEV_ID: [],
}

LANGSMITH_TAG_VALUES = {
    "ac11ac11-0001-4001-8001-ac11ac11ac11": [
        {"id": "ad11ad11-0001-4001-8001-ad11ad11ad11", "value": "prod"},
    ],
}

LANGSMITH_OAUTH_CLIENTS = {
    WORKSPACE_PROD_ID: {
        "clients": [
            {
                "id": "ae11ae11-0001-4001-8001-ae11ae11ae11",
                "client_id": "langsmith-mcp-client",
                "client_name": "Internal MCP Client",
                "client_type": "confidential",
                "client_uri": "https://tools.simpson.corp",
                "logo_uri": None,
                "policy_uri": None,
                "tos_uri": None,
                "redirect_uris": ["https://tools.simpson.corp/callback"],
                "allowed_scopes": ["runs:read", "projects:read"],
                "grant_types": ["authorization_code", "refresh_token"],
                "disabled": False,
                "created_at": "2026-02-05T09:00:00Z",
                "updated_at": "2026-02-05T09:00:00Z",
            },
        ],
    },
    WORKSPACE_DEV_ID: {"clients": []},
}

LANGSMITH_MCP_SERVERS = {
    WORKSPACE_PROD_ID: [
        {
            "id": "af11af11-0001-4001-8001-af11af11af11",
            "name": "Internal Docs",
            "slug": "internal-docs",
            "description": "Company documentation search.",
            "url": "https://mcp.simpson.corp/docs",
            "auth_type": "oauth",
            "status": "active",
            "tool_filter": {"allowed": ["search_docs", "get_doc"]},
            "created_at": "2026-02-06T09:00:00Z",
            "updated_at": "2026-02-06T09:00:00Z",
        },
    ],
    WORKSPACE_DEV_ID: [],
}

LANGSMITH_MCP_VENDORS: dict[str, list] = {"mcp_vendors": []}
