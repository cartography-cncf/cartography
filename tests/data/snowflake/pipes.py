"""Raw Snowflake pipe payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/pipes` returns them. The
auto-ingest pipe names the SNS topic that notifies it, which is the join back to
the AWS graph.
"""

from typing import Any

SNOWFLAKE_PIPES: list[dict[str, Any]] = [
    {
        "name": "DONUT_DELIVERY_PIPE",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "definition": "COPY INTO DONUT_DELIVERIES FROM @DONUT_STAGE",
        "copy_statement": "COPY INTO DONUT_DELIVERIES FROM @DONUT_STAGE",
        "pattern": ".*[.]csv",
        "integration": "DONUT_NOTIFY",
        "auto_ingest": True,
        "aws_sns_topic": "arn:aws:sns:us-east-1:000000000000:donut-deliveries",
        "error_integration": "MELTDOWN_ALERTS",
        "invalid_reason": None,
        "owner": "PLANT_ENGINEER",
        "comment": "Load the morning donut manifest",
        "created_on": "2026-08-03T16:10:00.000+00:00",
    },
    {
        "name": "SQUISHEE_PIPE",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "definition": None,
        "copy_statement": "COPY INTO SQUISHEE_SALES FROM @KWIK_E_STAGE",
        "pattern": None,
        "integration": None,
        "auto_ingest": False,
        "aws_sns_topic": None,
        "error_integration": None,
        "invalid_reason": "Target table SQUISHEE_SALES was dropped",
        "owner": "SHOPKEEPER",
        "comment": None,
        "created_on": "2026-08-03T16:12:00.000+00:00",
    },
]
