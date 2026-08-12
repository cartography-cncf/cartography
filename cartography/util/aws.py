"""AWS-specific helpers.

These live outside ``cartography.util`` so that importing the core package does
not pull ``boto3``/``botocore`` into every cartography process. Only code that
already talks to AWS should import from here.
"""

import asyncio
import logging
import warnings
from functools import partial
from functools import wraps
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import cast
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import TypeVar

import backoff
import boto3
import botocore
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import ReadTimeoutError
from botocore.parsers import ResponseParserError

from cartography.helpers import backoff_handler

logger = logging.getLogger(__name__)

R = TypeVar("R")

DEFAULT_MAX_PAGES = 10000


def is_service_control_policy_explicit_deny(
    error: botocore.exceptions.ClientError,
) -> bool:
    """Return True if the ClientError was caused by an explicit service control policy deny."""
    error_code = error.response.get("Error", {}).get("Code")
    if error_code not in {"AccessDenied", "AccessDeniedException"}:
        return False

    message = error.response.get("Error", {}).get("Message")
    if not message:
        return False

    lowered = message.lower()
    return "explicit deny" in lowered and "service control policy" in lowered


def aws_paginate(
    client: boto3.client,
    method_name: str,
    object_name: str,
    max_pages: int | None = DEFAULT_MAX_PAGES,
    **kwargs: Any,
) -> Iterable[Dict]:
    """
    Helper function for handling AWS boto3 API pagination with progress logging.

    This function provides a convenient wrapper around boto3's pagination
    functionality, with built-in progress logging and configurable page limits
    to prevent runaway API calls.

    Args:
        client: The boto3 client instance to use for API calls.
        method_name: The name of the boto3 client method to paginate.
        object_name: The key in the API response containing the list of items.
        max_pages: Maximum number of pages to fetch. None for unlimited.
                  Defaults to DEFAULT_MAX_PAGES.
        **kwargs: Additional keyword arguments to pass to the paginator.

    Yields:
        Individual items from the paginated API response.

    Examples:
        Paginating EC2 instances:
        >>> ec2_client = boto3.client('ec2')
        >>> for instance in aws_paginate(
        ...     ec2_client,
        ...     'describe_instances',
        ...     'Reservations'
        ... ):
        ...     print(instance)

        Paginating with filters and limits:
        >>> for bucket in aws_paginate(
        ...     s3_client,
        ...     'list_objects_v2',
        ...     'Contents',
        ...     max_pages=100,
        ...     Bucket='my-bucket',
        ...     Prefix='logs/'
        ... ):
        ...     print(bucket)

    Note:
        The function logs progress every 100 pages to help monitor long-running
        operations. If the specified object_name is not found in a response page,
        a warning is logged but iteration continues.

        The max_pages limit is enforced to prevent excessive API calls that
        could hit rate limits or take excessive time. A warning is logged
        when the limit is reached.
    """
    paginator = client.get_paginator(method_name)
    for i, page in enumerate(paginator.paginate(**kwargs), start=1):
        if i % 100 == 0:
            logger.debug("fetching page number %s", i)
        if object_name in page:
            items = page[object_name]
            yield from items
        else:
            logger.warning(
                f"""aws_paginate: Key "{object_name}" is not present, check if this is a typo.
If not, then the AWS datatype somehow does not have this key.""",
            )
        if max_pages is not None and i >= max_pages:
            logger.warning(f"Reached max batch size of {max_pages} pages")
            break


AWSGetFunc = TypeVar("AWSGetFunc", bound=Callable[..., Iterable])

# fix for AWS TooManyRequestsException
# Error codes that indicate a service is unavailable in a region or blocked by policies
AWS_REGION_ACCESS_DENIED_ERROR_CODES = [
    "AccessDenied",
    "AccessDeniedException",
    "AuthFailure",
    "AuthorizationError",
    "AuthorizationErrorException",
    "InvalidClientTokenId",
    "UnauthorizedOperation",
    "UnrecognizedClientException",
    "InternalServerErrorException",
    "SubscriptionRequiredException",
]

AWS_REGION_UNSUPPORTED_OPERATION_SNIPPETS = (
    "not supported in the called region",
    "not supported in this region",
    "unsupported in this region",
)


def _is_region_unsupported_unknown_operation(
    error_code: Optional[str],
    error_message: Optional[str],
) -> bool:
    """
    Return True for UnknownOperationException errors that explicitly indicate regional unavailability.
    """
    if error_code != "UnknownOperationException" or not error_message:
        return False
    lowered = error_message.lower()
    return any(
        snippet in lowered for snippet in AWS_REGION_UNSUPPORTED_OPERATION_SNIPPETS
    )


def is_aws_region_skippable_client_error(
    error: botocore.exceptions.ClientError,
) -> bool:
    """
    Return True when a ClientError indicates regional unavailability or regional access denial.

    This is the shared classification used by AWS sync code that needs to decide
    whether a regional failure should degrade to a regional skip instead of
    failing the account-level sync.
    """
    error_code = error.response.get("Error", {}).get("Code")
    error_message = error.response.get("Error", {}).get("Message")
    return (
        _is_region_unsupported_unknown_operation(
            error_code,
            error_message,
        )
        or error_code in AWS_REGION_ACCESS_DENIED_ERROR_CODES
    )


def aws_handle_regions(func: AWSGetFunc) -> AWSGetFunc:
    """
    Decorator to handle AWS regional access errors and opt-in region limitations.

    This decorator wraps AWS API functions to gracefully handle client errors
    that occur when accessing regions that are disabled, require opt-in, or
    where the account lacks necessary permissions. Instead of failing, the
    decorated function returns an empty list when these specific errors occur.

    The decorator also includes exponential backoff retry logic to handle
    AWS TooManyRequestsException and other transient errors that may occur
    during API calls.

    Args:
        func: An AWS API function that returns an iterable (typically a list)
              of resources. Should be a ``get_`` function that queries AWS services.

    Returns:
        The decorated function with error handling and retry logic applied.
        On handled errors, returns an empty list instead of raising exceptions.

    Examples:
        Decorating an AWS resource getter function:
        >>> @aws_handle_regions
        ... def get_ec2_instances(boto3_session, region):
        ...     ec2 = boto3_session.client('ec2', region_name=region)
        ...     return ec2.describe_instances()['Reservations']

    Note:
        The decorator handles these specific AWS error codes:
        - AccessDenied / AccessDeniedException
        - AuthFailure
        - AuthorizationError / AuthorizationErrorException
        - InvalidClientTokenId
        - UnauthorizedOperation
        - UnrecognizedClientException
        - InternalServerErrorException

        For these errors, a warning is logged and an empty list is returned.
        Other errors are re-raised normally.

        UnknownOperationException is only skipped when the error message
        explicitly indicates the operation is unsupported in the requested region.

        The decorator includes retry logic with exponential backoff (max 600 seconds)
        for handling transient AWS API errors and rate limiting.

        This should be used on functions that return lists of AWS resources
        and need to work across multiple regions, including those that may
        be disabled or require special permissions.
    """

    @wraps(func)
    # fix for AWS TooManyRequestsException
    # https://github.com/cartography-cncf/cartography/issues/297
    # https://github.com/cartography-cncf/cartography/issues/243
    # https://github.com/cartography-cncf/cartography/issues/65
    # https://github.com/cartography-cncf/cartography/issues/25
    @backoff.on_exception(
        backoff.expo,
        (botocore.exceptions.ClientError, ResponseParserError),
        max_time=600,
        on_backoff=backoff_handler,
    )
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")
            if error_code == "InvalidToken":
                raise RuntimeError(
                    "AWS returned an InvalidToken error. Configure regional STS endpoints by "
                    "setting environment variable AWS_STS_REGIONAL_ENDPOINTS=regional or adding "
                    "'sts_regional_endpoints = regional' to your AWS config file."
                ) from e
            # The account is not authorized to use this service in this region
            # or the service is unavailable in the region, so we can continue
            # without raising an exception.
            if is_aws_region_skippable_client_error(e):
                if is_service_control_policy_explicit_deny(e):
                    logger.warning(
                        "Service control policy denied access while calling %s: %s",
                        func.__name__,
                        error_message,
                    )
                else:
                    logger.warning(
                        "{} in this region. Skipping...".format(
                            error_message,
                        ),
                    )
                return []
            else:
                raise
        except EndpointConnectionError:
            logger.warning(
                "Encountered an EndpointConnectionError. This means that the AWS "
                "resource is not available in this region. Skipping.",
            )
            return []
        except (ConnectTimeoutError, ReadTimeoutError):
            logger.warning(
                "Encountered a timeout while calling a regional AWS endpoint. "
                "Skipping this region.",
            )
            return []

    return cast(AWSGetFunc, inner_function)


def is_throttling_exception(exc: Exception) -> bool:
    """
    Determine if an exception is caused by API rate limiting or throttling.

    This function checks whether a given exception indicates that an API call
    was throttled or rate-limited by the service provider. It currently supports
    AWS boto3 throttling exceptions and can be extended to support other cloud
    providers' throttling mechanisms.

    Args:
        exc: The exception to check for throttling indicators.

    Returns:
        True if the exception indicates throttling/rate limiting, False otherwise.

    Examples:
        Checking AWS boto3 exceptions:
        >>> import botocore.exceptions
        >>> try:
        ...     # AWS API call that might be throttled
        ...     s3_client.list_buckets()
        ... except Exception as e:
        ...     if is_throttling_exception(e):
        ...         print("Request was throttled, should retry")
        ...     else:
        ...         print("Different type of error occurred")

        Integration with backoff decorators:
        >>> @backoff.on_exception(
        ...     backoff.expo,
        ...     lambda e: is_throttling_exception(e),
        ...     max_tries=3
        ... )
        ... def resilient_api_call():
        ...     return api_client.get_data()

    Note:
        Currently supports these AWS error codes:
        - LimitExceededException: General rate limit exceeded
        - Throttling: Request rate too high

        The function can be extended to support other cloud providers like GCP
        (google.api_core.exceptions.TooManyRequests) or Azure as needed.

        This function is particularly useful in conjunction with retry decorators
        or custom retry logic to distinguish between transient throttling errors
        that should be retried and permanent errors that should not.

        See AWS documentation for more details on error handling:
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html
    """
    # https://boto3.amazonaws.com/v1/documentation/api/1.19.9/guide/error-handling.html
    if isinstance(exc, botocore.exceptions.ClientError):
        if exc.response["Error"]["Code"] in ["LimitExceededException", "Throttling"]:
            return True
    # add other exceptions here, if needed, like:
    # https://cloud.google.com/python/docs/reference/storage/1.39.0/retry_timeout#configuring-retries
    # if isinstance(exc, google.api_core.exceptions.TooManyRequests):
    #     return True
    return False


def to_asynchronous(func: Callable[..., R], *args: Any, **kwargs: Any) -> Awaitable[R]:
    """
    Execute a synchronous function asynchronously in a threadpool with throttling protection.

    This function wraps any synchronous callable to run in the default asyncio threadpool,
    making it awaitable. It includes built-in protection against throttling errors through
    automatic retry with exponential backoff. This is a transitional helper until we migrate
    to Python 3.9's asyncio.to_thread.

    Args:
        func: The synchronous function to execute asynchronously.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        An awaitable that resolves to the function's return value when executed.

    Examples:
        Converting a synchronous API call to async:
        >>> def fetch_data(endpoint, timeout=30):
        ...     return requests.get(endpoint, timeout=timeout).json()
        >>>
        >>> async def main():
        ...     # Run synchronous function asynchronously
        ...     future = to_asynchronous(fetch_data, "https://api.example.com/data", timeout=10)
        ...     data = await future
        ...     return data

    Note:
        Once Python 3.9+ is adopted, consider migrating to asyncio.to_thread()
        for similar functionality with native asyncio support.
    """
    CartographyThrottlingException = type(
        "CartographyThrottlingException",
        (Exception,),
        {},
    )

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if is_throttling_exception(exc):
                raise CartographyThrottlingException from exc
            raise

    # don't use @backoff as decorator, to preserve typing
    wrapped = backoff.on_exception(
        backoff.expo,
        CartographyThrottlingException,
        max_time=300,
    )(
        wrapper,
    )
    call = partial(wrapped, *args, **kwargs)
    return asyncio.get_event_loop().run_in_executor(None, call)


def to_synchronous(*awaitables: Awaitable[Any]) -> List[Any]:
    """
    Synchronously execute multiple awaitables and return their results.

    This function blocks the current thread until all provided awaitables complete,
    collecting their results into a list. It's designed for use in synchronous code
    that needs to execute async functions or consume results from async operations
    without converting the calling code to async.

    Args:
        *awaitables: Variable number of awaitable objects (Futures, coroutines, tasks).
                    Each awaitable is provided as a separate argument, not as a list.

    Returns:
        List containing the results of all awaitables in the same order they were
        provided. If any awaitable raises an exception, the entire operation fails.

    Examples:
        Executing multiple async functions synchronously:
        >>> async def fetch_user(user_id):
        ...     # Simulate async API call
        ...     await asyncio.sleep(0.1)
        ...     return f"User {user_id}"
        >>>
        >>> async def fetch_posts(user_id):
        ...     # Simulate another async API call
        ...     await asyncio.sleep(0.1)
        ...     return f"Posts for {user_id}"
        >>>
        >>> # Execute both async functions from sync code
        >>> user_future = fetch_user(123)
        >>> posts_future = fetch_posts(123)
        >>> results = to_synchronous(user_future, posts_future)
        >>> print(results)  # ['User 123', 'Posts for 123']

    Note:
        This function uses asyncio.gather() internally, which means:
        - All awaitables run concurrently
        - If any awaitable fails, the entire operation fails immediately
        - Results are returned in the same order as the input awaitables

        This is particularly useful for:
        - Legacy synchronous code that needs to call async functions
        - Testing async code in synchronous test frameworks
        - CLI scripts that need to orchestrate async operations
        - Bridge code between sync and async boundaries

        For error handling, consider using asyncio.gather(return_exceptions=True)
        if you need to handle individual failures gracefully. This function
        does not provide that option currently.

        Be aware that this function blocks the calling thread until all
        awaitables complete. For web applications or other async contexts,
        prefer using await directly with asyncio.gather().
    """
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="There is no current event loop",
                category=DeprecationWarning,
            )
            event_loop = asyncio.get_event_loop()
    except RuntimeError:
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)

    return event_loop.run_until_complete(asyncio.gather(*awaitables))
