"""Raw Snowflake notification integration payloads, as `GET /api/v2/notification-integrations` returns them."""

from typing import Any

SNOWFLAKE_NOTIFICATION_TOPIC_ARN = "arn:aws:sns:us-east-2:000000000000:reactor-alerts"
SNOWFLAKE_NOTIFICATION_ROLE_ARN = "arn:aws:iam::000000000000:role/SnowflakeSNSRole"

SNOWFLAKE_NOTIFICATION_INTEGRATIONS: list[dict[str, Any]] = [
    {
        "name": "REACTOR_ALERT_SNS",
        "enabled": True,
        "created_on": "2026-08-03T17:30:00.000+00:00",
        "comment": "Publishes reactor alerts to SNS",
        "notification_hook": {
            "type": "QUEUE_AWS_SNS_OUTBOUND",
            "aws_sns_topic_arn": SNOWFLAKE_NOTIFICATION_TOPIC_ARN,
            "aws_sns_role_arn": SNOWFLAKE_NOTIFICATION_ROLE_ARN,
            "aws_sns_external_id": "SPRINGFIELD_NUCLEAR_SFCRole=4_mnopqr==",
        },
    },
    {
        "name": "DONUT_PUBSUB",
        "enabled": True,
        "created_on": "2026-08-03T17:32:00.000+00:00",
        "comment": None,
        "notification_hook": {
            "type": "QUEUE_GCP_PUBSUB",
            "gcp_pubsub_subscription_name": (
                "projects/springfield/subscriptions/donut-events"
            ),
            "gcp_pubsub_topic_name": "projects/springfield/topics/donut-events",
        },
    },
    {
        "name": "MOE_EMAIL",
        "enabled": False,
        "created_on": "2026-08-03T17:33:00.000+00:00",
        "comment": None,
        "notification_hook": {"type": "EMAIL"},
    },
]
