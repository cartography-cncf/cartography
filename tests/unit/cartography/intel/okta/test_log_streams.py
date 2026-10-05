from cartography.intel.okta.log_streams import _transform_okta_log_streams
from tests.data.okta.log_streams import LOG_STREAMS


def test_transform_okta_log_streams() -> None:
    # Act
    log_streams = _transform_okta_log_streams(LOG_STREAMS)

    # Assert
    assert log_streams == [
        {
            "id": "0oa-eventbridge",
            "name": "Security data lake",
            "type": "aws_eventbridge",
            "status": "ACTIVE",
            "created": "2026-01-01T00:00:00.000Z",
            "okta_last_updated": "2026-02-01T00:00:00.000Z",
            "aws_account_id": "123456789012",
            "aws_region": "us-east-2",
            "aws_event_source_name": "okta-system-log",
            "splunk_host": None,
            "splunk_edition": None,
        },
        {
            "id": "0oa-splunk",
            "name": "SIEM",
            "type": "splunk_cloud_logstreaming",
            "status": "INACTIVE",
            "created": "2026-01-01T00:00:00.000Z",
            "okta_last_updated": "2026-03-01T00:00:00.000Z",
            "aws_account_id": None,
            "aws_region": None,
            "aws_event_source_name": None,
            "splunk_host": "example.splunkcloud.com",
            "splunk_edition": "aws",
        },
    ]
