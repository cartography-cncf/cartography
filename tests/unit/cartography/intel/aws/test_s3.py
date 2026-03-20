from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError

from cartography.intel.aws.s3 import get_s3_bucket_list


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
        403, {"x-amz-bucket-region": "ap-southeast-1"},
    )

    result = get_s3_bucket_list(mock_session)
    assert result["Buckets"][0]["Region"] == "ap-southeast-1"


@patch("cartography.intel.aws.s3._is_common_exception", return_value=(True, True))
def test_get_s3_bucket_list_common_exception_sets_region_none(mock_is_common):
    """A common exception (no region header) keeps the bucket and sets Region to None."""
    mock_session = MagicMock()
    mock_client = mock_session.client.return_value

    mock_client.list_buckets.return_value = {
        "Buckets": [{"Name": "bad-bucket"}],
    }
    mock_client.head_bucket.side_effect = _make_client_error(403)

    result = get_s3_bucket_list(mock_session)
    assert result["Buckets"][0]["Region"] is None
