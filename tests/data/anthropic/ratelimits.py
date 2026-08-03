ANTHROPIC_RATE_LIMITS = [
    {
        "type": "rate_limit",
        "group_type": "model_group",
        "models": ["claude-opus-5"],
        "limits": [
            {"type": "requests_per_minute", "value": 4000},
            {"type": "input_tokens_per_minute", "value": 400000},
        ],
    },
    {
        "type": "rate_limit",
        "group_type": "web_search",
        "models": None,
        "limits": [
            {"type": "requests_per_minute", "value": 1000},
        ],
    },
]

# Keyed by workspace id, as returned by
# GET /organizations/workspaces/{id}/rate_limits. Only overrides are returned; a
# group with no entry here inherits the organization limit rather than being
# unlimited.
ANTHROPIC_WORKSPACE_RATE_LIMITS = {
    "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ": [
        {
            "type": "workspace_rate_limit",
            "group_type": "model_group",
            "models": ["claude-opus-5"],
            "limits": [
                {
                    "type": "requests_per_minute",
                    "value": 500,
                    "org_limit": 4000,
                },
            ],
        },
    ],
}
