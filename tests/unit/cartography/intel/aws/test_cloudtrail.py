from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from cartography.intel.aws.cloudtrail import get_cloudtrail_trails


def _client_error(code: str, message: str, status_code: int) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": message},
            "ResponseMetadata": {"HTTPStatusCode": status_code},
        },
        "DescribeTrails",
    )


def test_get_cloudtrail_trails_skips_transient_describe_trails_failure():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.describe_trails.side_effect = _client_error(
        "503",
        "Service Unavailable",
        503,
    )

    trails = get_cloudtrail_trails(
        boto3_session,
        "us-east-1",
        "123456789012",
    )

    assert trails == []


def test_get_cloudtrail_trails_keeps_trail_when_event_selectors_temporarily_fail():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.describe_trails.return_value = {
        "trailList": [
            {
                "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/example",
                "HomeRegion": "us-east-1",
            }
        ]
    }
    client.get_event_selectors.side_effect = _client_error(
        "ServiceUnavailableException",
        "Service unavailable",
        503,
    )

    trails = get_cloudtrail_trails(
        boto3_session,
        "us-east-1",
        "123456789012",
    )

    assert trails == [
        {
            "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/example",
            "HomeRegion": "us-east-1",
            "EventSelectors": [],
            "AdvancedEventSelectors": [],
        }
    ]
