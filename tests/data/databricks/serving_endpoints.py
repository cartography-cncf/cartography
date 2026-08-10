# Shape returned by serving_endpoints.get() (the "endpoints" list). One
# Databricks-hosted foundation model and one external (third-party) model so
# the external_model_provider egress signal is exercised.
DATABRICKS_SERVING_ENDPOINTS = [
    {
        "name": "databricks-gpt-5-5",
        "endpoint_type": "FOUNDATION_MODEL_API",
        "task": "llm/v1/chat",
        "permission_level": "CAN_MANAGE",
        "creation_timestamp": 1776902400000,
        "last_updated_timestamp": 1776902400000,
        "state": {"ready": "READY", "config_update": "NOT_UPDATING"},
        "config": {
            "served_entities": [
                {
                    "name": "databricks-gpt-5-5",
                    "entity_name": "system.ai.databricks-gpt-5-5",
                    "type": "FOUNDATION_MODEL",
                    "foundation_model": {"name": "system.ai.databricks-gpt-5-5"},
                },
            ],
        },
    },
    {
        "name": "external-openai-proxy",
        "endpoint_type": "EXTERNAL_MODEL",
        "task": "llm/v1/chat",
        "creator": "jeremy@subimage.io",
        "creation_timestamp": 1782900000000,
        "last_updated_timestamp": 1782900000000,
        "state": {"ready": "READY", "config_update": "NOT_UPDATING"},
        "config": {
            "served_entities": [
                {
                    "name": "openai-gpt4",
                    "type": "EXTERNAL_MODEL",
                    "external_model": {"provider": "openai", "name": "gpt-4o"},
                },
            ],
        },
    },
]
