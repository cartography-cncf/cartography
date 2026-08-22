"""Raw Snowflake storage integration rows.

``SNOWFLAKE_STORAGE_INTEGRATIONS`` is shaped as `SHOW STORAGE INTEGRATIONS` returns it
and ``SNOWFLAKE_STORAGE_INTEGRATION_DETAILS`` as `DESC INTEGRATION` returns it once
folded into one dict per integration by ``SnowflakeClient.describe``. Every value is a
string because that is what the SQL API sends.
"""

from typing import Any

SNOWFLAKE_STORAGE_INTEGRATION_ROLE_ARN = (
    "arn:aws:iam::000000000000:role/SnowflakeStageRole"
)

SNOWFLAKE_STORAGE_INTEGRATIONS: list[dict[str, Any]] = [
    {
        "name": "PLANT_S3_INTEGRATION",
        "type": "EXTERNAL_STAGE",
        "category": "STORAGE",
        "enabled": "true",
        "comment": "Reads and writes the reactor log bucket",
        "created_on": "1784200000.000000000 0",
    },
    {
        "name": "SQUISHEE_AZURE_INTEGRATION",
        "type": "EXTERNAL_STAGE",
        "category": "STORAGE",
        "enabled": "false",
        "comment": "",
        "created_on": "1784300000.000000000 0",
    },
]

SNOWFLAKE_STORAGE_INTEGRATION_DETAILS: dict[str, Any] = {
    "PLANT_S3_INTEGRATION": {
        "enabled": "true",
        "storage_provider": "S3",
        # A bare bucket prefix: every stage on this integration can reach the whole
        # bucket, not just the telemetry path.
        "storage_allowed_locations": "s3://springfield-reactor-logs/",
        "storage_blocked_locations": "s3://springfield-reactor-logs/secrets/",
        "storage_aws_role_arn": SNOWFLAKE_STORAGE_INTEGRATION_ROLE_ARN,
        "storage_aws_iam_user_arn": "arn:aws:iam::999999999999:user/snowflake-stage",
        "storage_aws_external_id": "SPRINGFIELD_NUCLEAR_SFCRole=5_stuvwx==",
        "azure_tenant_id": "",
        "azure_multi_tenant_app_name": "",
        "use_privatelink_endpoint": "false",
        "comment": "Reads and writes the reactor log bucket",
    },
    "SQUISHEE_AZURE_INTEGRATION": {
        "enabled": "false",
        "storage_provider": "AZURE",
        "storage_allowed_locations": (
            "azure://springfieldkwikemart.blob.core.windows.net/squishee/"
        ),
        "storage_blocked_locations": "",
        "storage_aws_role_arn": "",
        "storage_aws_iam_user_arn": "",
        "storage_aws_external_id": "",
        "azure_tenant_id": "11111111-1111-1111-1111-111111111111",
        "azure_multi_tenant_app_name": "snowflakepacint_1700000000000",
        "use_privatelink_endpoint": "true",
        "comment": "",
    },
}
