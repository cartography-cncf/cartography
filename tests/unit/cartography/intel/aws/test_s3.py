from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError

from cartography.intel.aws.s3 import FETCH_FAILED
from cartography.intel.aws.s3 import get_public_access_block
from cartography.intel.aws.s3 import get_s3_bucket_list
from cartography.intel.aws.s3 import preserve_s3_buckets_with_failed_region_discovery


def _make_client_error(status_code, headers=None):
    """Build a ClientError with the given HTTP status and optional headers."""
    error_response = {
        "Error": {"Code": str(status_code), "Message": "Forbidden"},
        "ResponseMetadata": {
            "HTTPStatusCode": status_code,
            "HTTPHeaders": headers or {},
        },
    }
    return ClientError(error_response, "HeadBucket")


def test_get_s3_bucket_list_happy_path():
    """head_bucket succeeds and returns BucketRegion directly."""
    mock_session = MagicMock()
    mock_client = mock_session.client.return_value

    mock_client.list_buckets.return_value = {
        "Buckets": [{"Name": "my-bucket"}],
    }
    mock_client.head_bucket.return_value = {
        "BucketRegion": "us-west-2",
        "ResponseMetadata": {"HTTPHeaders": {}},
    }

    result = get_s3_bucket_list(mock_session)
    assert result["Buckets"][0]["Region"] == "us-west-2"


def test_get_s3_bucket_list_region_from_header():
    """head_bucket succeeds but BucketRegion is missing; falls back to x-amz-bucket-region header."""
    mock_session = MagicMock()
    mock_client = mock_session.client.return_value

    mock_client.list_buckets.return_value = {
        "Buckets": [{"Name": "my-bucket"}],
    }
    mock_client.head_bucket.return_value = {
        "BucketRegion": None,
        "ResponseMetadata": {
            "HTTPHeaders": {"x-amz-bucket-region": "eu-central-1"},
        },
    }

    result = get_s3_bucket_list(mock_session)
    assert result["Buckets"][0]["Region"] == "eu-central-1"


def test_get_s3_bucket_list_403_with_region_header():
    """head_bucket returns 403 but the error response includes x-amz-bucket-region."""
    mock_session = MagicMock()
    mock_client = mock_session.client.return_value

    mock_client.list_buckets.return_value = {
        "Buckets": [{"Name": "forbidden-bucket"}],
    }
    mock_client.head_bucket.side_effect = _make_client_error(
        403,
        {"x-amz-bucket-region": "ap-southeast-1"},
    )

    result = get_s3_bucket_list(mock_session)
    assert result["Buckets"][0]["Region"] == "ap-southeast-1"


@patch("cartography.intel.aws.s3._is_common_exception", return_value=(True, True))
def test_get_s3_bucket_list_common_exception_preserves_failed_bucket(mock_is_common):
    """A common exception without region data skips the bucket and marks it for preservation."""
    mock_session = MagicMock()
    mock_client = mock_session.client.return_value

    mock_client.list_buckets.return_value = {
        "Buckets": [{"Name": "bad-bucket"}],
    }
    mock_client.head_bucket.side_effect = _make_client_error(403)

    result = get_s3_bucket_list(mock_session)
    assert result["Buckets"] == []
    assert [bucket["Name"] for bucket in result["FailedBuckets"]] == ["bad-bucket"]


def test_get_s3_bucket_list_connect_timeout_preserves_other_buckets():
    """A timeout on one bucket should not stop region discovery for surrounding buckets."""
    mock_session = MagicMock()
    mock_client = mock_session.client.return_value

    mock_client.list_buckets.return_value = {
        "Buckets": [
            {"Name": "first-bucket"},
            {"Name": "slow-bucket"},
            {"Name": "last-bucket"},
        ],
    }
    mock_client.head_bucket.side_effect = [
        {
            "BucketRegion": "us-east-1",
            "ResponseMetadata": {"HTTPHeaders": {}},
        },
        ConnectTimeoutError(
            endpoint_url="https://slow-bucket.s3.me-south-1.amazonaws.com/",
            error="timed out",
        ),
        {
            "BucketRegion": "eu-west-1",
            "ResponseMetadata": {"HTTPHeaders": {}},
        },
    ]

    result = get_s3_bucket_list(mock_session)
    assert result["Buckets"] == [
        {"Name": "first-bucket", "Region": "us-east-1"},
        {"Name": "last-bucket", "Region": "eu-west-1"},
    ]
    assert [bucket["Name"] for bucket in result["FailedBuckets"]] == ["slow-bucket"]


def test_preserve_s3_buckets_with_failed_region_discovery_updates_existing_state():
    neo4j_session = MagicMock()

    preserve_s3_buckets_with_failed_region_discovery(
        neo4j_session,
        [{"Name": "slow-bucket", "CreationDate": "2026-04-24T00:00:00Z"}],
        "123456789012",
        42,
    )

    assert neo4j_session.execute_write.call_count == 3


def test_get_public_access_block_connect_timeout_preserves_existing_data():
    bucket = {"Name": "slow-bucket"}
    client = MagicMock()
    client.get_public_access_block.side_effect = ConnectTimeoutError(
        endpoint_url="https://slow-bucket.s3.me-south-1.amazonaws.com/?publicAccessBlock",
        error="timed out",
    )

    assert get_public_access_block(bucket, client) is FETCH_FAILED


def test_get_public_access_block_retryable_client_error_preserves_existing_data():
    bucket = {"Name": "slow-bucket"}
    client = MagicMock()
    client.get_public_access_block.side_effect = ClientError(
        {
            "Error": {"Code": "ServiceUnavailable", "Message": "Unknown"},
            "ResponseMetadata": {"HTTPStatusCode": 503},
        },
        "GetPublicAccessBlock",
    )

    assert get_public_access_block(bucket, client) is FETCH_FAILED
