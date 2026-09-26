from tests.data.langsmith.workspaces import WORKSPACE_DEV_ID
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID

SUPPORT_DEPLOYMENT_ID = "aa11aa11-0001-4001-8001-aa11aa11aa11"
TRIAGE_DEPLOYMENT_ID = "aa11aa11-0002-4002-8002-aa11aa11aa11"

SUPPORT_AGENT_ID = "agent-support-bot"
TRIAGE_AGENT_ID = "agent-triage-bot"

LANGSMITH_DEPLOYMENTS = {
    WORKSPACE_PROD_ID: [
        {
            "id": SUPPORT_DEPLOYMENT_ID,
            "tenant_id": WORKSPACE_PROD_ID,
            "name": "support-bot",
            "display_name": "Support Bot",
            "status": "READY",
            "url": "https://support-bot.us.langgraph.app",
            "source": "github",
            "image_version": "v1.4.2",
            # Shared outside the organization: a finding worth querying for.
            "shareable": True,
            "route_through_gateway": True,
            "is_managed_deep_agent": False,
            "is_preview": False,
            "tracer_session_id": "bb22bb22-0001-4001-8001-bb22bb22bb22",
            "created_at": "2026-02-01T09:00:00Z",
            "updated_at": "2026-03-01T09:00:00Z",
            "agent": {"agent_id": SUPPORT_AGENT_ID, "environment": "production"},
            # Secret VALUES are present in the API response and must never reach the graph.
            "secrets": [
                {"name": "OPENAI_API_KEY", "value": "SENTINEL-MUST-NOT-BE-INGESTED"},
                {"name": "SLACK_BOT_TOKEN", "value": "SENTINEL-MUST-NOT-BE-INGESTED"},
            ],
            "secret_references": [
                {
                    "name": "DB_PASSWORD",
                    "secret_name": "prod-db",
                    "secret_key": "password",
                },
            ],
        },
    ],
    WORKSPACE_DEV_ID: [
        {
            "id": TRIAGE_DEPLOYMENT_ID,
            "tenant_id": WORKSPACE_DEV_ID,
            "name": "triage-bot",
            "display_name": "Triage Bot",
            "status": "READY",
            "url": "https://triage-bot.us.langgraph.app",
            "source": "external_docker",
            "image_version": "v0.9.0",
            "shareable": False,
            "route_through_gateway": False,
            "is_managed_deep_agent": True,
            "is_preview": False,
            "tracer_session_id": None,
            "created_at": "2026-02-02T09:00:00Z",
            "updated_at": "2026-03-02T09:00:00Z",
            # Most real deployments carry no agent block; credentials attach to the
            # deployment itself in that case.
            "agent": None,
            "secrets": [],
            "secret_references": [],
        },
    ],
}

# Assistants served on each deployment's own data plane, keyed by deployment URL. The
# support deployment also declares its agent in an agent block, so its record is merged;
# the triage deployment has agent: null, so its agent is only discoverable this way.
LANGSMITH_ASSISTANTS = {
    "https://support-bot.us.langgraph.app": [
        {
            "assistant_id": SUPPORT_AGENT_ID,
            "graph_id": "support_graph",
            "name": "Support Bot",
            "description": "Answers customer support tickets.",
            "version": 3,
            "created_at": "2026-02-01T09:05:00Z",
            "updated_at": "2026-03-01T09:05:00Z",
        },
    ],
    "https://triage-bot.us.langgraph.app": [
        {
            "assistant_id": TRIAGE_AGENT_ID,
            "graph_id": "triage_graph",
            "name": "Triage Bot",
            "description": "Routes incoming issues.",
            "version": 1,
            "created_at": "2026-02-02T09:05:00Z",
            "updated_at": "2026-03-02T09:05:00Z",
        },
    ],
}
