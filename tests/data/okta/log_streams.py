from typing import Any

# Synthetic raw API payloads for GET /api/v1/logStreams.

LOG_STREAMS: list[dict[str, Any]] = [
    {
        "id": "0oa-eventbridge",
        "type": "aws_eventbridge",
        "name": "Security data lake",
        "status": "ACTIVE",
        "created": "2026-01-01T00:00:00.000Z",
        "lastUpdated": "2026-02-01T00:00:00.000Z",
        "settings": {
            "accountId": "123456789012",
            "eventSourceName": "okta-system-log",
            "region": "us-east-2",
        },
        "_links": {},
    },
    {
        # The API never returns the Splunk HEC token.
        "id": "0oa-splunk",
        "type": "splunk_cloud_logstreaming",
        "name": "SIEM",
        "status": "INACTIVE",
        "created": "2026-01-01T00:00:00.000Z",
        "lastUpdated": "2026-03-01T00:00:00.000Z",
        "settings": {"host": "example.splunkcloud.com", "edition": "aws"},
        "_links": {},
    },
]
