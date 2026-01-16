from datetime import datetime
from datetime import timezone
from unittest import mock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import botocore
import pytest
from googleapiclient.errors import HttpError

import cartography.util
from cartography import util
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import GCP_API_MAX_RETRIES
from cartography.intel.gcp.util import is_retryable_gcp_http_error
from cartography.util import aws_handle_regions
from cartography.util import batch
from cartography.util import is_service_control_policy_explicit_deny
from cartography.util import run_analysis_and_ensure_deps
from cartography.util import to_datetime


def test_run_analysis_job_default_package(mocker):
    mocker.patch("cartography.util.GraphJob")
    read_text_mock = mocker.patch("cartography.util.read_text")
    util.run_analysis_job("test.json", mocker.Mock(), mocker.Mock())
    read_text_mock.assert_called_once_with(
        "cartography.data.jobs.analysis",
        "test.json",
    )


def test_run_analysis_job_custom_package(mocker):
    mocker.patch("cartography.util.GraphJob")
    read_text_mock = mocker.patch("cartography.util.read_text")
    util.run_analysis_job("test.json", mocker.Mock(), mocker.Mock(), package="a.b.c")
    read_text_mock.assert_called_once_with("a.b.c", "test.json")


def test_run_scoped_analysis_job_default_package(mocker):
    mocker.patch("cartography.util.GraphJob")
    read_text_mock = mocker.patch("cartography.util.read_text")
    util.run_scoped_analysis_job("test.json", mocker.Mock(), mocker.Mock())
    read_text_mock.assert_called_once_with(
        "cartography.data.jobs.scoped_analysis",
        "test.json",
    )


@patch(
    "cartography.util.backoff",
    Mock(
        on_exception=lambda *args, **kwargs: lambda func: func,
    ),
)
def test_aws_handle_regions(mocker):
    # no exception
    @aws_handle_regions
    def happy_path(a, b):
        return a + b

    assert happy_path(1, 2) == 3

    # returns the default on_exception_return_value=[]
    @aws_handle_regions
    def raises_supported_client_error(a, b):
        e = botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "aws_handle_regions is not working",
                },
            },
            "FakeOperation",
        )
        raise e

    assert raises_supported_client_error(1, 2) == []

    # AuthorizationError should also return the default
    @aws_handle_regions
    def raises_authorization_error(a, b):
        e = botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "AuthorizationError",
                    "Message": "aws_handle_regions is not working",
                },
            },
            "FakeOperation",
        )
        raise e

    assert raises_authorization_error(1, 2) == []

    # InvalidToken should raise RuntimeError
    @aws_handle_regions
    def raises_invalid_token(a, b):
        e = botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "InvalidToken",
                    "Message": "token invalid",
                },
            },
            "FakeOperation",
        )
        raise e

    with pytest.raises(RuntimeError):
        raises_invalid_token(1, 2)

    # unhandled type of ClientError
    @aws_handle_regions
    def raises_unsupported_client_error(a, b):
        e = botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": ">9000",
                    "Message": "aws_handle_regions is not working",
                },
            },
            "FakeOperation",
        )
        raise e

    with pytest.raises(botocore.exceptions.ClientError):
        raises_unsupported_client_error(1, 2)

    # other type of error besides ClientError
    @aws_handle_regions
    def raises_unsupported_error(a, b):
        return a / 0

    with pytest.raises(ZeroDivisionError):
        raises_unsupported_error(1, 2)


def test_is_service_control_policy_explicit_deny():
    scp_error = botocore.exceptions.ClientError(
        {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "User: arn:aws:sts::123456789012:assumed-role/MyRole/session-12345 "
                "is not authorized to perform: inspector2:ListFindings on resource: "
                "arn:aws:inspector2:us-east-1:123456789012:/findings/list with an explicit deny in a service control policy",
            },
        },
        "ListFindings",
    )
    assert is_service_control_policy_explicit_deny(scp_error) is True

    # Regular access denied without SCP
    regular_access_denied = botocore.exceptions.ClientError(
        {
            "Error": {
                "Code": "AccessDenied",
                "Message": "User is not authorized to perform this action",
            },
        },
        "SomeOperation",
    )
    assert is_service_control_policy_explicit_deny(regular_access_denied) is False


def test_batch(mocker):
    # Arrange
    x = range(12)
    expected = [
        [0, 1, 2, 3, 4],
        [5, 6, 7, 8, 9],
        [10, 11],
    ]
    # Act
    actual = list(batch(x, 5))
    # Assert
    assert actual == expected
    # Also check for empty input
    assert list(batch([], 3)) == []


def test_batch_generator():
    # Arrange
    def my_generator():
        yield from range(12)

    x = my_generator()
    expected = [
        [0, 1, 2, 3, 4],
        [5, 6, 7, 8, 9],
        [10, 11],
    ]
    # Act
    actual = list(batch(x, 5))
    # Assert
    assert actual == expected
    # Also check for empty generator
    assert list(batch((i for i in range(0)), 3)) == []


@mock.patch.object(cartography.util, "run_analysis_job", return_value=None)
def test_run_analysis_and_ensure_deps(mock_run_analysis_job: mock.MagicMock):
    # Arrange
    neo4j_session = mock.MagicMock()
    common_job_parameters = mock.MagicMock()

    # This arg doesn't matter for this test
    requested_syncs = {
        "ec2:instance",
        "iam",
        "resourcegroupstaggingapi",
    }

    # Act
    ec2_asset_exposure_requirements = {
        "ec2:instance",
        "ec2:security_group",
        "ec2:load_balancer",
        "ec2:load_balancer_v2",
    }
    run_analysis_and_ensure_deps(
        "aws_ec2_asset_exposure.json",
        ec2_asset_exposure_requirements,
        requested_syncs,
        common_job_parameters,
        neo4j_session,
    )

    # Assert that the analysis job was not called because the requested sync reqs aren't met
    mock_run_analysis_job.assert_not_called()


@mock.patch.object(cartography.util, "run_analysis_job", return_value=None)
def test_run_analysis_and_ensure_deps_no_requirements(
    mock_run_analysis_job: mock.MagicMock,
):
    # Arrange
    neo4j_session = mock.MagicMock()
    common_job_parameters = mock.MagicMock()

    # This arg doesn't matter for this test
    requested_syncs = {
        "ec2:instance",
        "iam",
        "resourcegroupstaggingapi",
    }

    # Act
    run_analysis_and_ensure_deps(
        "aws_foreign_accounts.json",
        {"iam"},
        requested_syncs,
        common_job_parameters,
        neo4j_session,
    )

    # Assert
    mock_run_analysis_job.assert_called_once_with(
        "aws_foreign_accounts.json",
        neo4j_session,
        common_job_parameters,
    )


def test_aws_handle_regions_retries_on_response_parser_error(mocker):
    """Test that aws_handle_regions retries on ResponseParserError.

    ResponseParserError occurs when AWS returns invalid XML responses (e.g., "Internal Failure"
    as plain text instead of XML). This is a transient AWS infrastructure issue.
    """
    from botocore.parsers import ResponseParserError

    call_count = 0

    @aws_handle_regions
    def fails_then_succeeds():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ResponseParserError("Unable to parse response")
        return "success"

    # Mock sleep to avoid actual delays
    mocker.patch("time.sleep")

    result = fails_then_succeeds()
    assert result == "success"
    assert call_count == 3


def test_to_datetime_none_returns_none():
    """Test that None input returns None."""
    assert to_datetime(None) is None


def test_to_datetime_python_datetime_returns_same():
    """Test that a Python datetime is returned unchanged."""
    dt = datetime(2025, 1, 15, 10, 36, 31, tzinfo=timezone.utc)
    result = to_datetime(dt)
    assert result is dt


def test_to_datetime_neo4j_datetime_with_to_native():
    """Test conversion of neo4j.time.DateTime using to_native() method."""
    expected = datetime(2025, 1, 15, 10, 36, 31, tzinfo=timezone.utc)

    # Mock neo4j.time.DateTime with to_native method
    mock_neo4j_dt = MagicMock()
    mock_neo4j_dt.to_native.return_value = expected

    result = to_datetime(mock_neo4j_dt)

    assert result == expected
    mock_neo4j_dt.to_native.assert_called_once()


def test_to_datetime_neo4j_datetime_fallback_attributes():
    """Test fallback conversion using datetime attributes when to_native is not available."""
    # Mock neo4j.time.DateTime without to_native method
    mock_neo4j_dt = MagicMock(
        spec=[
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "second",
            "nanosecond",
            "tzinfo",
        ]
    )
    mock_neo4j_dt.year = 2025
    mock_neo4j_dt.month = 1
    mock_neo4j_dt.day = 15
    mock_neo4j_dt.hour = 10
    mock_neo4j_dt.minute = 36
    mock_neo4j_dt.second = 31
    mock_neo4j_dt.nanosecond = 0
    mock_neo4j_dt.tzinfo = timezone.utc

    result = to_datetime(mock_neo4j_dt)

    assert result == datetime(2025, 1, 15, 10, 36, 31, tzinfo=timezone.utc)


def test_to_datetime_neo4j_datetime_fallback_with_nanoseconds():
    """Test fallback conversion properly converts nanoseconds to microseconds."""
    mock_neo4j_dt = MagicMock(
        spec=[
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "second",
            "nanosecond",
            "tzinfo",
        ]
    )
    mock_neo4j_dt.year = 2025
    mock_neo4j_dt.month = 1
    mock_neo4j_dt.day = 15
    mock_neo4j_dt.hour = 10
    mock_neo4j_dt.minute = 36
    mock_neo4j_dt.second = 31
    mock_neo4j_dt.nanosecond = 500000000  # 500 milliseconds = 500000 microseconds
    mock_neo4j_dt.tzinfo = timezone.utc

    result = to_datetime(mock_neo4j_dt)

    assert result.microsecond == 500000


def test_to_datetime_neo4j_datetime_fallback_default_timezone():
    """Test that fallback uses UTC when tzinfo is None."""
    mock_neo4j_dt = MagicMock(
        spec=[
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "second",
            "nanosecond",
            "tzinfo",
        ]
    )
    mock_neo4j_dt.year = 2025
    mock_neo4j_dt.month = 1
    mock_neo4j_dt.day = 15
    mock_neo4j_dt.hour = 10
    mock_neo4j_dt.minute = 36
    mock_neo4j_dt.second = 31
    mock_neo4j_dt.nanosecond = 0
    mock_neo4j_dt.tzinfo = None

    result = to_datetime(mock_neo4j_dt)

    assert result.tzinfo == timezone.utc


def test_to_datetime_unsupported_type_raises_error():
    """Test that unsupported types raise TypeError."""
    with pytest.raises(TypeError, match="Cannot convert str to datetime"):
        to_datetime("not a datetime")


def test_to_datetime_unsupported_type_int_raises_error():
    """Test that integer raises TypeError."""
    with pytest.raises(TypeError, match="Cannot convert int to datetime"):
        to_datetime(12345)


def test_is_retryable_gcp_http_error_503():
    """Test that HTTP 503 is identified as retryable."""
    mock_resp = MagicMock()
    mock_resp.status = 503
    error = HttpError(mock_resp, b"Service Unavailable")

    assert is_retryable_gcp_http_error(error) is True


def test_is_retryable_gcp_http_error_429():
    """Test that HTTP 429 (rate limit) is identified as retryable."""
    mock_resp = MagicMock()
    mock_resp.status = 429
    error = HttpError(mock_resp, b"Rate Limit Exceeded")

    assert is_retryable_gcp_http_error(error) is True


def test_is_retryable_gcp_http_error_5xx():
    """Test that HTTP 5xx errors are identified as retryable."""
    for status_code in [500, 502, 503, 504]:
        mock_resp = MagicMock()
        mock_resp.status = status_code
        error = HttpError(mock_resp, b"Server Error")
        assert (
            is_retryable_gcp_http_error(error) is True
        ), f"Expected {status_code} to be retryable"


def test_is_retryable_gcp_http_error_4xx_not_retryable():
    """Test that HTTP 4xx errors (except 429) are NOT identified as retryable."""
    for status_code in [400, 401, 403, 404]:
        mock_resp = MagicMock()
        mock_resp.status = status_code
        error = HttpError(mock_resp, b"Client Error")
        assert (
            is_retryable_gcp_http_error(error) is False
        ), f"Expected {status_code} to NOT be retryable"


def test_is_retryable_gcp_http_error_non_http_error():
    """Test that non-HttpError exceptions are not retryable."""
    assert is_retryable_gcp_http_error(ValueError("test")) is False
    assert is_retryable_gcp_http_error(RuntimeError("test")) is False


def test_gcp_api_execute_with_retry_success():
    """Test successful execution without retry."""
    mock_request = MagicMock()
    mock_request.execute.return_value = {"items": ["data"]}

    result = gcp_api_execute_with_retry(mock_request)

    assert result == {"items": ["data"]}
    mock_request.execute.assert_called_once()


def test_gcp_api_execute_with_retry_retries_on_503(mocker):
    """Test that 503 errors trigger retries."""
    mock_resp = MagicMock()
    mock_resp.status = 503

    mock_request = MagicMock()
    mock_request.execute.side_effect = [
        HttpError(mock_resp, b"Service Unavailable"),
        {"items": ["data"]},
    ]

    # Mock sleep to avoid delays
    mocker.patch("time.sleep")

    result = gcp_api_execute_with_retry(mock_request)

    assert result == {"items": ["data"]}
    assert mock_request.execute.call_count == 2


def test_gcp_api_execute_with_retry_gives_up_on_403():
    """Test that 403 errors are not retried and are raised immediately."""
    mock_resp = MagicMock()
    mock_resp.status = 403

    mock_request = MagicMock()
    mock_request.execute.side_effect = HttpError(mock_resp, b"Forbidden")

    with pytest.raises(HttpError):
        gcp_api_execute_with_retry(mock_request)

    # Should only be called once since 403 is not retryable
    mock_request.execute.assert_called_once()


def test_gcp_api_execute_with_retry_exhausts_retries(mocker):
    """Test that after max retries, the error is raised."""
    mock_resp = MagicMock()
    mock_resp.status = 503

    mock_request = MagicMock()
    mock_request.execute.side_effect = HttpError(mock_resp, b"Service Unavailable")

    # Mock sleep to avoid delays
    mocker.patch("time.sleep")

    with pytest.raises(HttpError):
        gcp_api_execute_with_retry(mock_request)

    # Should be called max_retries times
    assert mock_request.execute.call_count == GCP_API_MAX_RETRIES
