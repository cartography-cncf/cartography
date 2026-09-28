"""Raw Snowflake catalog integration payloads, as `GET /api/v2/catalog-integrations` returns them."""

from typing import Any

SNOWFLAKE_CATALOG_INTEGRATION_ROLE_ARN = (
    "arn:aws:iam::000000000000:role/SnowflakeGlueRole"
)

SNOWFLAKE_CATALOG_INTEGRATIONS: list[dict[str, Any]] = [
    {
        "name": "SPRINGFIELD_GLUE_CATALOG",
        "enabled": True,
        "table_format": "ICEBERG",
        "type": "GLUE",
        "category": "CATALOG",
        "created_on": "2026-08-03T17:20:00.000+00:00",
        "comment": "Reads the Glue catalog for monorail telemetry",
        "catalog": {
            "catalog_source": "GLUE",
            "glue_aws_role_arn": SNOWFLAKE_CATALOG_INTEGRATION_ROLE_ARN,
            "glue_aws_iam_user_arn": "arn:aws:iam::999999999999:user/snowflake-glue",
            "glue_catalog_id": "000000000000",
            "glue_region": "us-east-2",
            "catalog_namespace": "monorail",
        },
    },
    # An Iceberg REST catalog authenticated with OAuth. The client secret is never
    # returned by Snowflake and is never stored.
    {
        "name": "DUFF_REST_CATALOG",
        "enabled": False,
        "table_format": "ICEBERG",
        "type": "ICEBERG_REST",
        "category": "CATALOG",
        "created_on": "2026-08-03T17:22:00.000+00:00",
        "comment": None,
        "catalog": {
            "catalog_source": "POLARIS",
            "catalog_namespace": "duff",
            "rest_config": {
                "catalog_uri": "https://catalog.duff.example.com/v1",
                "warehouse": "duff_warehouse",
            },
            "rest_authentication": {
                "type": "OAUTH",
                "oauth_client_id": "duff-catalog-client",
                "oauth_allowed_scopes": ["PRINCIPAL_ROLE:ALL"],
            },
        },
    },
]
