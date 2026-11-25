from tests.data.langsmith.deployments import SUPPORT_DEPLOYMENT_ID
from tests.data.langsmith.deployments import SUPPORT_TRACING_PROJECT_ID
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID

PROD_TAG_VALUE_ID = "ad11ad11-0001-4001-8001-ad11ad11ad11"
ACCESS_POLICY_ID = "ab11ab11-0001-4001-8001-ab11ab11ab11"
DOCS_MCP_SERVER_ID = "af11af11-0001-4001-8001-af11af11af11"
CHECKOUT_PROJECT_ID = "ba11ba11-0001-4001-8001-ba11ba11ba11"
SCRATCH_PROJECT_ID = "ba11ba11-0002-4002-8002-ba11ba11ba11"

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
            "id": ACCESS_POLICY_ID,
            "name": "Production projects only",
            "description": "Restricts the auditor role to production-tagged projects.",
            "effect": "allow",
            "role_ids": [CUSTOM_ROLE_ID],
            "condition_groups": [
                {
                    "permission": "runs:read",
                    "resource_type": "project",
                    "conditions": [
                        {
                            "attribute_name": "resource_tag_key",
                            "attribute_key": "environment",
                            "operator": "equals",
                            "attribute_value": "prod",
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
        {"id": PROD_TAG_VALUE_ID, "value": "prod"},
    ],
}

LANGSMITH_PROJECTS = {
    WORKSPACE_PROD_ID: [
        {
            "id": CHECKOUT_PROJECT_ID,
            "tenant_id": WORKSPACE_PROD_ID,
            "name": "checkout-agent",
            "description": "Production checkout agent traces.",
            "start_time": "2026-02-01T09:00:00Z",
            "trace_tier": "longlived",
            "reference_dataset_id": None,
        },
        {
            "id": SCRATCH_PROJECT_ID,
            "tenant_id": WORKSPACE_PROD_ID,
            "name": "scratch",
            "description": None,
            "start_time": "2026-02-02T09:00:00Z",
            "trace_tier": "shortlived",
            "reference_dataset_id": None,
        },
        {
            # The tracing project the support-bot deployment writes runs to.
            "id": SUPPORT_TRACING_PROJECT_ID,
            "tenant_id": WORKSPACE_PROD_ID,
            "name": "support-bot",
            "description": None,
            "start_time": "2026-02-01T09:00:00Z",
            "trace_tier": "longlived",
            "reference_dataset_id": None,
        },
    ],
    WORKSPACE_DEV_ID: [],
}

# The taggings listing groups each tag value's resources by type.
LANGSMITH_TAGGINGS = {
    WORKSPACE_PROD_ID: [
        {
            "tag_key": "environment",
            "tag_key_id": "ac11ac11-0001-4001-8001-ac11ac11ac11",
            "tag_value": "prod",
            "tag_value_id": PROD_TAG_VALUE_ID,
            "resources": {
                "projects": [
                    {
                        "tagging_id": "bb11bb11-0001-4001-8001-bb11bb11bb11",
                        "resource_id": CHECKOUT_PROJECT_ID,
                        "resource_name": "checkout-agent",
                    },
                ],
                "deployments": [
                    {
                        "tagging_id": "bb11bb11-0002-4002-8002-bb11bb11bb11",
                        "resource_id": SUPPORT_DEPLOYMENT_ID,
                        "resource_name": "support-bot",
                    },
                ],
                "datasets": [],
                "prompts": [],
            },
        },
    ],
    WORKSPACE_DEV_ID: [],
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

# MCP gateways are listed per vendor, so the vendor listing comes first.
LANGSMITH_MCP_VENDORS = {
    WORKSPACE_PROD_ID: {"mcp_vendors": [{"vendor_id": "arcade", "name": "Arcade"}]},
    WORKSPACE_DEV_ID: {"mcp_vendors": []},
}

LANGSMITH_MCP_SERVERS = {
    "arcade": [
        {
            "id": DOCS_MCP_SERVER_ID,
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
}
