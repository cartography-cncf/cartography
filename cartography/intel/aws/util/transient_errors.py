from botocore.exceptions import ClientError
from botocore.exceptions import ConnectionClosedError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import ReadTimeoutError
from botocore.parsers import ResponseParserError

RETRYABLE_HTTP_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
RETRYABLE_AWS_ERROR_CODES = frozenset(
    {
        "InternalFailure",
        "InternalServerException",
        "RequestLimitExceeded",
        "RequestThrottled",
        "RequestTimeout",
        "RequestTimeoutException",
        "ServiceException",
        "ServiceUnavailable",
        "ServiceUnavailableException",
        "Throttling",
        "ThrottlingException",
        "TooManyRequestsException",
    },
)
TRANSIENT_REGION_EXCEPTIONS = (
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
    ResponseParserError,
)


def is_retryable_aws_client_error(
    error: ClientError,
) -> bool:
    error_code = error.response.get("Error", {}).get("Code", "")
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return (
        error_code in RETRYABLE_AWS_ERROR_CODES
        or status_code in RETRYABLE_HTTP_STATUS_CODES
    )
