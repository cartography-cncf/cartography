DATABRICKS_WORKSPACE_HOST = "https://dbc-aaeaddda-e52f.cloud.databricks.com"
DATABRICKS_WORKSPACE_ID = "1234567890123456"

DATABRICKS_WORKSPACE_CONF = {
    "enableTokensConfig": "true",
    "maxTokenLifetimeDays": "730",
}

DATABRICKS_WORKSPACE = {
    "id": DATABRICKS_WORKSPACE_ID,
    "workspace_id": DATABRICKS_WORKSPACE_ID,
    "legacy_id": "dbc-aaeaddda-e52f.cloud.databricks.com",
    "host": DATABRICKS_WORKSPACE_HOST,
    "tokens_enabled": True,
    "max_token_lifetime_days": 730,
}


def scoped(scim_id: str) -> str:
    return f"{DATABRICKS_WORKSPACE_ID}/{scim_id}"
