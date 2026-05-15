import inspect
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectionClosedError
from botocore.exceptions import ConnectTimeoutError

from cartography.intel.aws.cloudtrail import CloudTrailTransientRegionFailure
from cartography.intel.aws.cloudtrail import get_cloudtrail_trails
from cartography.intel.aws.cloudtrail import sync
from cartography.intel.aws.util.botocore_config import get_botocore_config


def _client_error(code: str, message: str, status_code: int) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": message},
            "ResponseMetadata": {"HTTPStatusCode": status_code},
        },
        "DescribeTrails",
    )


def test_get_cloudtrail_trails_raises_transient_region_failure_on_describe_trails_failure():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.describe_trails.side_effect = _client_error(
        "ServiceUnavailable",
        "Service Unavailable",
        503,
    )

    with pytest.raises(CloudTrailTransientRegionFailure):
        get_cloudtrail_trails(
            boto3_session,
            "us-east-1",
            "123456789012",
        )


def test_get_cloudtrail_trails_uses_shared_retry_profile():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.describe_trails.return_value = {"trailList": []}

    get_cloudtrail_trails(
        boto3_session,
        "us-east-1",
        "123456789012",
    )

    assert boto3_session.client.call_args.kwargs["config"] == get_botocore_config()


def test_get_cloudtrail_trails_raises_transient_region_failure_when_event_selectors_temporarily_fail():
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

    with pytest.raises(CloudTrailTransientRegionFailure):
        get_cloudtrail_trails(
            boto3_session,
            "us-east-1",
            "123456789012",
        )


def test_get_cloudtrail_trails_raises_non_retryable_client_error():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.describe_trails.side_effect = _client_error(
        "ValidationException",
        "Bad request",
        400,
    )

    get_cloudtrail_trails_unwrapped = inspect.unwrap(get_cloudtrail_trails)

    with pytest.raises(ClientError):
        get_cloudtrail_trails_unwrapped(
            boto3_session,
            "us-east-1",
            "123456789012",
        )


def test_get_cloudtrail_trails_raises_transient_region_failure_on_transport_timeout():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.describe_trails.side_effect = ConnectTimeoutError(
        endpoint_url="https://cloudtrail.us-east-1.amazonaws.com",
    )

    with pytest.raises(CloudTrailTransientRegionFailure):
        get_cloudtrail_trails(
            boto3_session,
            "us-east-1",
            "123456789012",
        )


def test_get_cloudtrail_trails_raises_transient_region_failure_on_connection_closed():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.describe_trails.side_effect = ConnectionClosedError(
        endpoint_url="https://cloudtrail.us-east-1.amazonaws.com",
        request=None,
    )

    with pytest.raises(CloudTrailTransientRegionFailure):
        get_cloudtrail_trails(
            boto3_session,
            "us-east-1",
            "123456789012",
        )


def test_sync_skips_cleanup_after_transient_region_failure(mocker):
    get_cloudtrail = mocker.patch(
        "cartography.intel.aws.cloudtrail.get_cloudtrail_trails",
        side_effect=CloudTrailTransientRegionFailure("temporary failure"),
    )
    cleanup = mocker.patch("cartography.intel.aws.cloudtrail.cleanup")
    load_cloudtrail = mocker.patch(
        "cartography.intel.aws.cloudtrail.load_cloudtrail_trails"
    )

    sync(
        MagicMock(),
        MagicMock(),
        ["us-east-1"],
        "123456789012",
        1,
        {},
    )

    get_cloudtrail.assert_called_once()
    load_cloudtrail.assert_not_called()
    cleanup.assert_not_called()


def test_sync_loads_successful_region_and_skips_cleanup_after_mixed_region_results(
    mocker,
):
    successful_region_trails = [
        {
            "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/example",
            "HomeRegion": "us-east-1",
            "EventSelectors": [],
            "AdvancedEventSelectors": [],
        }
    ]

    def _get_cloudtrail_trails_side_effect(_, region, __):
        if region == "us-east-1":
            return successful_region_trails
        raise CloudTrailTransientRegionFailure("temporary failure")

    get_cloudtrail = mocker.patch(
        "cartography.intel.aws.cloudtrail.get_cloudtrail_trails",
        side_effect=_get_cloudtrail_trails_side_effect,
    )
    cleanup = mocker.patch("cartography.intel.aws.cloudtrail.cleanup")
    load_cloudtrail = mocker.patch(
        "cartography.intel.aws.cloudtrail.load_cloudtrail_trails"
    )

    sync(
        MagicMock(),
        MagicMock(),
        ["us-east-1", "us-west-2"],
        "123456789012",
        1,
        {},
    )

    assert get_cloudtrail.call_count == 2
    load_cloudtrail.assert_called_once_with(
        mocker.ANY,
        successful_region_trails,
        "us-east-1",
        "123456789012",
        1,
    )
    cleanup.assert_not_called()
