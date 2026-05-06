PORTKEY_USERS = [
    {
        "object": "user",
        "id": "user-1",
        "first_name": "Lisa",
        "last_name": "Simpson",
        "role": "owner",
        "email": "lisa@springfield.example",
        "created_at": "2024-01-25T11:35:07Z",
        "last_updated_at": "2024-01-25T11:35:07Z",
    },
    {
        "object": "user",
        "id": "user-2",
        "first_name": "Maggie",
        "last_name": "Simpson",
        "role": "member",
        "email": "maggie@springfield.example",
        "created_at": "2024-01-26T11:35:07Z",
        "last_updated_at": "2024-01-26T11:35:07Z",
    },
]

PORTKEY_WORKSPACES = [
    {
        "id": "ws-eng",
        "object": "workspace",
        "slug": "ws-eng",
        "name": "Engineering",
        "description": "Primary workspace",
        "created_at": "2024-07-30T13:27:29.000Z",
        "last_updated_at": "2024-07-30T13:27:29.000Z",
    }
]

PORTKEY_WORKSPACE_MEMBERS = {
    "ws-eng": [
        {
            "id": "user-1",
            "role": "admin",
            "org_role": "owner",
            "status": "active",
            "created_at": "2024-01-25T11:35:07Z",
            "last_updated_at": "2024-01-25T11:35:07Z",
        },
        {
            "id": "user-2",
            "role": "member",
            "org_role": "member",
            "status": "active",
            "created_at": "2024-01-26T11:35:07Z",
            "last_updated_at": "2024-01-26T11:35:07Z",
        },
    ],
}

PORTKEY_INVITES = [
    {
        "object": "invite",
        "id": "invite-1",
        "email": "bart@springfield.example",
        "role": "member",
        "created_at": "2024-02-01T10:00:00Z",
        "expires_at": "2024-02-08T10:00:00Z",
        "accepted_at": None,
        "status": "pending",
        "invited_by": "user-1",
        "workspaces": [{"workspace_id": "ws-eng", "role": "member"}],
    }
]

PORTKEY_API_KEYS = [
    {"id": "pk-1"},
]

PORTKEY_API_KEY_DETAILS = {
    "pk-1": {
        "id": "pk-1",
        "object": "api-key",
        "key": "pk****",
        "name": "Engineering API key",
        "description": "Workspace key",
        "type": "workspace-service",
        "organisation_id": "org-portkey",
        "workspace_id": "ws-eng",
        "user_id": "user-1",
        "status": "active",
        "created_at": "2023-09-15T10:30:00Z",
        "last_updated_at": "2023-09-15T10:30:00Z",
        "creation_mode": "ui",
        "rate_limits": [{"type": "requests", "unit": "rpm", "value": 100}],
        "usage_limits": {"credit_limit": 10, "periodic_reset": "monthly"},
        "reset_usage": 0,
        "scopes": ["logs.view"],
        "defaults": {"workspace_id": "ws-eng"},
        "alert_emails": ["alerts@springfield.example"],
        "expires_at": None,
    }
}

PORTKEY_VIRTUAL_KEYS = [
    {
        "object": "virtual-key",
        "slug": "vk-eng",
        "name": "Engineering VK",
        "note": "OpenAI access",
        "status": "active",
        "workspace_id": "ws-eng",
        "usage_limits": {"credit_limit": 10},
        "reset_usage": 0,
        "created_at": "2023-11-07T05:31:56Z",
        "model_config": {"provider": "openai"},
        "rate_limits": [{"type": "requests", "unit": "rpd", "value": 123}],
        "expires_at": None,
    }
]

PORTKEY_CONFIGS = [
    {
        "id": "cfg-1",
        "name": "Default Config",
        "slug": "cfg-default",
        "organisation_id": "org-portkey",
        "workspace_id": "ws-eng",
        "is_default": 1,
        "status": "active",
        "owner_id": "user-1",
        "updated_by": "user-2",
        "created_at": "2024-05-12T21:37:06.000Z",
        "last_updated_at": "2024-05-23T23:36:06.000Z",
    }
]

PORTKEY_SECRET_REFERENCES = [
    {
        "id": "secret-ref-1",
        "object": "secret-reference",
        "slug": "aws-openai",
        "name": "AWS OpenAI Key",
        "description": "Externalized provider secret",
        "manager_type": "aws_sm",
        "secret_path": "prod/openai",
        "secret_key": "api_key",
        "status": "active",
        "allow_all_workspaces": True,
        "auth_config": {"aws_region": "us-east-1"},
    }
]

PORTKEY_INTEGRATIONS = [
    {
        "id": "int-openai",
        "object": "integration",
        "organisation_id": "org-portkey",
        "workspace_id": "ws-eng",
        "ai_provider_id": "openai",
        "name": "OpenAI Production",
        "status": "active",
        "created_at": "2023-11-07T05:31:56Z",
        "last_updated_at": "2023-11-07T05:31:56Z",
        "slug": "openai-production",
        "description": "Primary OpenAI integration",
        "secret_mappings": [{"target_field": "key", "secret_reference_id": "secret-ref-1"}],
    }
]

PORTKEY_MCP_INTEGRATIONS = [
    {
        "id": "mcp-int-1",
        "name": "Atlassian MCP",
        "owner_id": "user-1",
        "status": "active",
        "type": "workspace",
        "url": "https://mcp.atlassian.example",
        "auth_type": "oauth_auto",
        "transport": "http",
        "configurations": {"scopes": ["read:jira"]},
        "created_at": "2023-11-07T05:31:56Z",
        "last_updated_at": "2023-11-07T05:31:56Z",
        "slug": "atlassian-mcp",
        "workspace_id": "ws-eng",
        "description": "Atlassian MCP integration",
        "workspaces_count": 1,
    }
]

PORTKEY_MCP_SERVERS = {
    "ws-eng": [
        {
            "id": "mcp-server-1",
            "organisation_id": "org-portkey",
            "name": "Atlassian Workspace Server",
            "description": "Workspace-scoped MCP server",
            "status": "active",
            "created_at": "2023-11-07T05:31:56Z",
            "owner_id": "user-1",
            "slug": "atlassian-server",
            "workspace_id": "ws-eng",
            "mcp_integration_id": "mcp-int-1",
            "mcp_integration_slug": "atlassian-mcp",
            "mcp_integration_url": "https://mcp.atlassian.example",
            "auth_type": "oauth_auto",
            "workspace_name": "Engineering",
            "workspace_slug": "ws-eng",
            "url": "https://mcp.atlassian.example/server",
        }
    ]
}

PORTKEY_PROVIDERS = {
    "ws-eng": [
        {
            "object": "provider",
            "slug": "provider-openai",
            "name": "OpenAI Workspace",
            "note": "workspace provider",
            "status": "active",
            "integration_id": "int-openai",
            "workspace_id": "ws-eng",
            "usage_limits": {"credit_limit": 10},
            "reset_usage": 0,
            "created_at": "2023-11-07T05:31:56Z",
            "rate_limits": [{"type": "requests", "unit": "rpd", "value": 123}],
            "expires_at": None,
        }
    ]
}

PORTKEY_GUARDRAILS = [
    {
        "id": "gr-1",
        "name": "JWT Guard",
        "slug": "jwt-guard",
        "organisation_id": "org-portkey",
        "workspace_id": "ws-eng",
        "status": "active",
        "created_at": "2023-11-07T05:31:56Z",
        "last_updated_at": "2023-11-07T05:31:56Z",
        "owner_id": "user-1",
        "updated_by": "user-2",
        "checks": [{"id": "default.jwt"}],
        "actions": {"deny": False},
    }
]

PORTKEY_PROMPT_COLLECTIONS = {
    "ws-eng": [
        {
            "id": "col-1",
            "name": "Core Prompts",
            "workspace_id": "ws-eng",
            "slug": "core-prompts",
            "parent_collection_id": None,
            "is_default": True,
            "status": "active",
            "created_at": "2023-11-07T05:31:56Z",
            "last_updated_at": "2023-11-07T05:31:56Z",
            "collection_details": {"prompts_count": 1},
        }
    ]
}

PORTKEY_PROMPTS = {
    "ws-eng": [
        {
            "id": "prompt-1",
            "object": "prompt",
            "slug": "summarize",
            "name": "Summarize",
            "collection_id": "col-1",
            "model": "gpt-4.1",
            "status": "active",
            "created_at": "2023-11-07T05:31:56Z",
            "last_updated_at": "2023-11-07T05:31:56Z",
        }
    ]
}
