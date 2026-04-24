from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError

from cartography.intel.aws.s3 import cleanup_s3_bucket_exposure_details
from cartography.intel.aws.s3 import FETCH_FAILED
from cartography.intel.aws.s3 import get_public_access_block
from cartography.intel.aws.s3 import get_s3_bucket_list
from cartography.intel.aws.s3 import load_s3_details
from cartography.intel.aws.s3 import preserve_s3_buckets_with_transient_failures


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


@patch("cartography.intel.aws.s3.run_write_query")
def test_preserve_s3_buckets_with_transient_failures_updates_existing_state(
    mock_run_write_query,
):
    neo4j_session = MagicMock()

    preserve_s3_buckets_with_transient_failures(
        neo4j_session,
        ["slow-bucket"],
        ["acl-bucket"],
        ["policy-bucket"],
        "123456789012",
        42,
    )

    assert mock_run_write_query.call_count == 3
    assert "MERGE (b:S3Bucket" not in mock_run_write_query.call_args_list[0].args[1]
    assert mock_run_write_query.call_args_list[0].kwargs["bucket_names"] == [
        "slow-bucket"
    ]
    assert mock_run_write_query.call_args_list[1].kwargs["bucket_names"] == [
        "acl-bucket",
        "slow-bucket",
    ]
    assert mock_run_write_query.call_args_list[2].kwargs["bucket_names"] == [
        "policy-bucket",
        "slow-bucket",
    ]


@patch("cartography.intel.aws.s3.GraphJob.run", autospec=True)
def test_cleanup_s3_bucket_exposure_details_uses_iterative_cleanup(mock_graph_job_run):
    neo4j_session = MagicMock()

    cleanup_s3_bucket_exposure_details(
        neo4j_session,
        "123456789012",
        ["slow-bucket"],
    )

    job = mock_graph_job_run.call_args.args[0]
    statement = job.statements[0]
    assert statement.iterative is True
    assert statement.iterationsize == 100
    assert statement.parameters["AWS_ID"] == "123456789012"
    assert statement.parameters["preserved_bucket_names"] == ["slow-bucket"]


@patch("cartography.intel.aws.s3.preserve_s3_buckets_with_transient_failures")
@patch("cartography.intel.aws.s3._load_s3_policy_statements")
@patch("cartography.intel.aws.s3._load_s3_acls")
@patch("cartography.intel.aws.s3.load")
@patch("cartography.intel.aws.s3.cleanup_s3_bucket_exposure_details")
def test_load_s3_details_preserves_resolved_bucket_policy_and_acl_failures(
    mock_cleanup_exposure,
    mock_load,
    mock_load_acls,
    mock_load_policy_statements,
    mock_preserve_transient_failures,
):
    neo4j_session = MagicMock()
    bucket_data = {
        "Buckets": [
            {
                "Name": "slow-bucket",
                "Region": "me-south-1",
                "CreationDate": "2026-04-24T00:00:00Z",
            }
        ],
        "FailedBuckets": [],
    }
    s3_details_iter = iter(
        [
            (
                "slow-bucket",
                FETCH_FAILED,
                FETCH_FAILED,
                FETCH_FAILED,
                FETCH_FAILED,
                FETCH_FAILED,
                FETCH_FAILED,
                FETCH_FAILED,
            )
        ]
    )

    load_s3_details(
        neo4j_session,
        s3_details_iter,
        bucket_data,
        "123456789012",
        42,
    )

    mock_cleanup_exposure.assert_called_once_with(
        neo4j_session,
        "123456789012",
        ["slow-bucket"],
    )
    mock_preserve_transient_failures.assert_called_once_with(
        neo4j_session,
        [],
        ["slow-bucket"],
        ["slow-bucket"],
        "123456789012",
        42,
    )
    assert mock_load.call_count == 1
    mock_load_acls.assert_called_once_with(neo4j_session, [], "123456789012", 42)
    mock_load_policy_statements.assert_called_once_with(
        neo4j_session,
        [],
        42,
        "123456789012",
    )


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
