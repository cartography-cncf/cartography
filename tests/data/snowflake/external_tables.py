"""Raw `SHOW EXTERNAL TABLES IN DATABASE` rows.

The SQL API returns every cell as a string keyed by the lowercased column name. The
`stage` reference arrives prefixed with `@`, as Snowflake writes stage references.
"""

from typing import Any

SNOWFLAKE_EXTERNAL_TABLES: list[dict[str, Any]] = [
    {
        "created_on": "1785010000.000000000 0",
        "name": "PLANT_LOGS",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "invalid": "false",
        "invalid_reason": None,
        "owner": "PLANT_ENGINEER",
        "comment": "Raw control-room logs still sitting in S3",
        "stage": "@SPRINGFIELD.NUCLEAR_PLANT.LOG_STAGE",
        "location": "s3://springfield-plant-logs/control-room/",
        "file_format_name": "SPRINGFIELD.NUCLEAR_PLANT.LOG_CSV",
        "file_format_type": "CSV",
        "cloud": "AWS",
        "region": "us-east-2",
        "notification_channel": "arn:aws:sqs:us-east-2:123456789012:sf-snowpipe",
        "last_refreshed_on": "1785013600.000000000 0",
        "table_format": None,
        "owner_role_type": "ROLE",
    },
    # Invalidated, and with no resolvable stage or file format reference.
    {
        "created_on": "1785010060.000000000 0",
        "name": "DONUT_SHIPMENTS",
        "database_name": "SPRINGFIELD",
        "schema_name": "KWIK_E_MART",
        "invalid": "true",
        "invalid_reason": "Storage location is no longer reachable",
        "owner": "SHOPKEEPER",
        "comment": None,
        "stage": "",
        "location": "s3://kwik-e-mart-shipments/",
        "file_format_name": "",
        "file_format_type": "JSON",
        "cloud": "AWS",
        "region": "us-east-2",
        "notification_channel": None,
        "last_refreshed_on": None,
        "table_format": "DELTA",
        "owner_role_type": "ROLE",
    },
]
