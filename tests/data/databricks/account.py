DATABRICKS_ACCOUNT_ID = "d80c5dcd-9c2d-42df-9d56-ccf551c8f9ed"
DATABRICKS_ACCOUNT_HOST = "https://accounts.cloud.databricks.com"

DATABRICKS_ACCOUNT = {
    "id": DATABRICKS_ACCOUNT_ID,
    "account_id": DATABRICKS_ACCOUNT_ID,
    "host": DATABRICKS_ACCOUNT_HOST,
}


def account_scoped(scim_id: str) -> str:
    return f"{DATABRICKS_ACCOUNT_ID}/{scim_id}"
