import asyncio
import logging
import re
from datetime import datetime
from datetime import timezone
from functools import partial
from functools import wraps
from importlib.resources import open_binary
from importlib.resources import read_text
from itertools import islice
from string import Template
from typing import Any
from typing import Awaitable
from typing import BinaryIO
from typing import Callable
from typing import cast
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Type
from typing import TypeVar
from typing import Union

import backoff
import boto3
import botocore
import neo4j
from botocore.exceptions import EndpointConnectionError
from botocore.parsers import ResponseParserError

from cartography.graph.job import GraphJob
from cartography.graph.statement import get_job_shortname
from cartography.stats import get_stats_client
from cartography.stats import ScopedStatsClient

logger = logging.getLogger(__name__)


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


STATUS_SUCCESS = 0
STATUS_FAILURE = 1
STATUS_KEYBOARD_INTERRUPT = 130
DEFAULT_BATCH_SIZE = 1000
DEFAULT_MAX_PAGES = 10000


def run_analysis_job(
    filename: str,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
    package: str = "cartography.data.jobs.analysis",
) -> None:
    """
    Execute an analysis job to enrich existing graph data.

    This function is designed for use with the cartography.intel.analysis sync stage.
    It runs queries from the specified Python package directory to perform analysis
    operations on the complete graph data. Analysis jobs are intended to run at the
    end of a full graph sync and apply to all resources across all accounts/projects.

    Args:
        filename: Name of the JSON file containing the analysis job queries.
        neo4j_session: Active Neo4j session for executing the analysis queries.
        common_job_parameters: Dictionary containing common parameters used across
                              all cartography jobs (e.g., update_tag).
        package: Python package containing the analysis job files.
                Defaults to "cartography.data.jobs.analysis".

    Examples:
        Running a standard analysis job:
        >>> run_analysis_job(
        ...     "aws_foreign_accounts.json",
        ...     neo4j_session,
        ...     {"UPDATE_TAG": 1234567890}
        ... )

        Running analysis from custom package:
        >>> run_analysis_job(
        ...     "custom_analysis.json",
        ...     neo4j_session,
        ...     common_params,
        ...     package="my_company.analysis_jobs"
        ... )

    Note:
        Analysis jobs are unscoped and apply to ALL resources in the graph
        (all AWS accounts, all GCP projects, all Okta organizations, etc.).
        For scoped analysis, use run_scoped_analysis_job() instead.

        The job file must be a valid JSON file containing GraphJob-compatible
        query definitions.
    """
    GraphJob.run_from_json(
        neo4j_session,
        read_text(
            package,
            filename,
        ),
        common_job_parameters,
        get_job_shortname(filename),
    )


def run_analysis_and_ensure_deps(
    analysis_job_name: str,
    resource_dependencies: Set[str],
    requested_syncs: Set[str],
    common_job_parameters: Dict[str, Any],
    neo4j_session: neo4j.Session,
) -> None:
    """
    Conditionally run an analysis job based on resource dependency requirements.

    This function checks if all required resource dependencies have been included
    in the requested syncs before executing the analysis job. This ensures that
    analysis jobs only run when their prerequisite data is available in the graph.

    Args:
        analysis_job_name: The filename of the analysis job to run (e.g., "aws_foreign_accounts.json").
        resource_dependencies: Set of resource sync names that must be completed
                              for this analysis job to run. Use empty set if no dependencies.
        requested_syncs: Set of resource sync names that were requested in the
                        current cartography execution.
        common_job_parameters: Dictionary containing common job parameters used
                              across cartography jobs.
        neo4j_session: Active Neo4j session for executing the analysis queries.

    Examples:
        Running analysis with AWS dependencies:
        >>> run_analysis_and_ensure_deps(
        ...     "aws_foreign_accounts.json",
        ...     {"aws:ec2", "aws:iam"},
        ...     {"aws:ec2", "aws:iam", "aws:s3"},
        ...     common_params,
        ...     neo4j_session
        ... )
        # Will run because all dependencies are satisfied

        Skipping analysis due to missing dependencies:
        >>> run_analysis_and_ensure_deps(
        ...     "gcp_analysis.json",
        ...     {"gcp:compute", "gcp:iam"},
        ...     {"aws:ec2"},  # Missing GCP dependencies
        ...     common_params,
        ...     neo4j_session
        ... )
        # Will skip and log warning

        Running analysis with no dependencies:
        >>> run_analysis_and_ensure_deps(
        ...     "general_analysis.json",
        ...     set(),  # No dependencies
        ...     {"aws:ec2"},
        ...     common_params,
        ...     neo4j_session
        ... )
        # Will always run

    Note:
        If dependencies are not satisfied, the function logs an informational
        message and returns without executing the analysis job. This prevents
        analysis jobs from running on incomplete data which could produce
        misleading results.
    """
    if not resource_dependencies.issubset(requested_syncs):
        logger.info(
            f"Did not run {analysis_job_name} because it needs {resource_dependencies} to be included "
            f"as a requested sync. You specified: {requested_syncs}. If you want this job to run, please change your "
            f"CLI args/cartography config so that all required resources are included.",
        )
        return

    run_analysis_job(
        analysis_job_name,
        neo4j_session,
        common_job_parameters,
    )


def run_scoped_analysis_job(
    filename: str,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
    package: str = "cartography.data.jobs.scoped_analysis",
) -> None:
    """
    Execute a scoped analysis job on a specific sub-resource.

    This function runs analysis queries that are scoped to a particular sub-resource
    (e.g., a specific AWS account) rather than across the entire graph. This is
    useful for analysis that should be performed within the context of a single
    organizational unit or account.

    Args:
        filename: Name of the JSON file containing the scoped analysis job queries.
        neo4j_session: Active Neo4j session for executing the analysis queries.
        common_job_parameters: Dictionary containing common parameters including
                              scope-specific identifiers (e.g., AWS account ID).
        package: Python package containing the scoped analysis job files.
                Defaults to "cartography.data.jobs.scoped_analysis".

    Examples:
        Running scoped analysis for AWS account:
        >>> common_params = {
        ...     "UPDATE_TAG": 1234567890,
        ...     "AWS_ID": "123456789012"
        ... }
        >>> run_scoped_analysis_job(
        ...     "aws_account_security.json",
        ...     neo4j_session,
        ...     common_params
        ... )

        Running scoped analysis from custom package:
        >>> run_scoped_analysis_job(
        ...     "gcp_project_analysis.json",
        ...     neo4j_session,
        ...     common_params,
        ...     package="my_company.scoped_jobs"
        ... )

    Note:
        Scoped analysis jobs are limited to data within a specific scope
        (typically defined by parameters like AWS_ID, GCP_PROJECT_ID, etc.).
        This is in contrast to global analysis jobs that operate across
        all resources. See the queries in cartography.data.jobs.scoped_analysis
        for specific examples of scoped analysis patterns.
    """
    run_analysis_job(
        filename,
        neo4j_session,
        common_job_parameters,
        package,
    )


def run_cleanup_job(
    filename: str,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
    package: str = "cartography.data.jobs.cleanup",
) -> None:
    """
    Execute a cleanup job to remove stale data from the graph.

    .. deprecated::
        This function is deprecated. For resources that have migrated to the new
        data model, use GraphJob directly instead of this wrapper function.

    This function runs cleanup queries that identify and remove nodes and
    relationships that are no longer current based on update timestamps.
    Cleanup jobs are essential for maintaining data freshness and preventing
    the accumulation of stale data in the graph.

    Args:
        filename: Name of the JSON file containing the cleanup job queries.
        neo4j_session: Active Neo4j session for executing the cleanup queries.
        common_job_parameters: Dictionary containing common parameters including
                              the update_tag used to identify stale data.
        package: Python package containing the cleanup job files.
                Defaults to "cartography.data.jobs.cleanup".

    Examples:
        Running standard cleanup job:
        >>> run_cleanup_job(
        ...     "aws_ec2_cleanup.json",
        ...     neo4j_session,
        ...     {"UPDATE_TAG": 1234567890}
        ... )

        Running cleanup from custom package:
        >>> run_cleanup_job(
        ...     "custom_cleanup.json",
        ...     neo4j_session,
        ...     common_params,
        ...     package="my_company.cleanup_jobs"
        ... )

    Note:
        Cleanup jobs typically use the UPDATE_TAG parameter to identify
        nodes and relationships that haven't been updated in the current
        sync cycle. These stale items are then removed to maintain data
        accuracy. Cleanup jobs should be run after all data ingestion
        stages are complete.

        For resources migrated to the new data model, prefer using GraphJob
        directly rather than this wrapper function to ensure compatibility
        with current cartography patterns and to avoid potential deprecation
        issues in future versions.
    """
    GraphJob.run_from_json(
        neo4j_session,
        read_text(
            package,
            filename,
        ),
        common_job_parameters,
        get_job_shortname(filename),
    )


def merge_module_sync_metadata(
    neo4j_session: neo4j.Session,
    group_type: str,
    group_id: Union[str, int],
    synced_type: str,
    update_tag: int,
    stat_handler: ScopedStatsClient,
) -> None:
    """
    Create or update ModuleSyncMetadata nodes to track sync operations.

    This function creates ModuleSyncMetadata nodes that record when specific
    resource types were synchronized within a particular scope. This metadata
    is used for tracking sync completeness and data freshness.

    Args:
        neo4j_session: Active Neo4j session for executing the metadata update.
        group_type: The parent module's node label (e.g., 'AWSAccount').
        group_id: The unique identifier of the parent module instance.
        synced_type: The sub-module's node label that was synced (e.g., 'S3Bucket').
        update_tag: Timestamp used to determine data freshness.
        stat_handler: StatsD client for sending metrics about the sync operation.

    Examples:
        Recording S3 bucket sync for an AWS account:
        >>> merge_module_sync_metadata(
        ...     neo4j_session,
        ...     group_type="AWSAccount",
        ...     group_id="123456789012",
        ...     synced_type="S3Bucket",
        ...     update_tag=1234567890,
        ...     stat_handler=stats_client
        ... )

    Note:
        The function creates a unique ModuleSyncMetadata node with an ID
        constructed from the group_type, group_id, and synced_type. This
        ensures one metadata record per sync scope. The function also
        sends a StatsD metric with the update timestamp for monitoring.

        The 'types' used should be actual Neo4j node labels present in
        the graph schema.
    """
    # Import here to avoid circular import with cartography.client.core.tx
    from cartography.client.core.tx import run_write_query

    template = Template(
        """
        MERGE (n:ModuleSyncMetadata{id:'${group_type}_${group_id}_${synced_type}'})
        ON CREATE SET
            n:SyncMetadata, n.firstseen=timestamp()
        SET n.syncedtype='${synced_type}',
            n.grouptype='${group_type}',
            n.groupid='${group_id}',
            n.lastupdated=$UPDATE_TAG
    """,
    )
    run_write_query(
        neo4j_session,
        template.safe_substitute(
            group_type=group_type,
            group_id=group_id,
            synced_type=synced_type,
        ),
        UPDATE_TAG=update_tag,
    )
    stat_handler.incr(f"{group_type}_{group_id}_{synced_type}_lastupdated", update_tag)


def load_resource_binary(package: str, resource_name: str) -> BinaryIO:
    """
    Load a binary resource from a Python package.

    This function provides a convenient way to load binary files (like images,
    compiled data, etc.) that are packaged with cartography modules.

    Args:
        package: The Python package name containing the resource.
        resource_name: The filename of the binary resource to load.

    Returns:
        A binary file-like object that can be read from.

    Examples:
        Loading indexes for Neo4j:
        >>> binary_data = load_resource_binary(
        ...     "cartography.data",
        ...     "indexes.cypher"
        ... )
        >>> content = binary_data.read()

    Note:
        This function uses importlib.resources.open_binary() under the hood,
        which works with both traditional file-system packages and newer
        importlib-based resource systems. The returned file object should
        be properly closed after use.
    """
    return open_binary(package, resource_name)


R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])


def timeit(method: F) -> F:
    """
    Decorator to measure and report function execution time via StatsD.

    This decorator automatically measures the execution time of the wrapped
    function and sends the timing data to a StatsD server if StatsD is enabled
    in the cartography configuration. The metric name is derived from the
    function's module and name.

    Args:
        method: The function to be timed and measured.

    Returns:
        The decorated function with timing instrumentation.

    Examples:
        Decorating a function for timing:
        >>> @timeit
        ... def expensive_operation():
        ...     # Complex processing here
        ...     return result

    Note:
        The decorator only performs timing when StatsD is enabled in the
        cartography configuration. When disabled, it simply calls the
        original function without any overhead.

        The timing metric is sent with the pattern:
        {module_name}.{function_name}

        The decorator preserves the original function's signature and
        metadata using functools.wraps, making it transparent to
        inspection tools and integration tests.
    """

    # Allow access via `inspect` to the wrapped function. This is used in integration tests to standardize param names.
    @wraps(method)
    def timed(*args, **kwargs):  # type: ignore
        stats_client = get_stats_client(method.__module__)
        if stats_client.is_enabled():
            timer = stats_client.timer(method.__name__)
            timer.start()
            result = method(*args, **kwargs)
            timer.stop()
            return result
        else:
            # statsd is disabled, so don't time anything
            return method(*args, **kwargs)

    return cast(F, timed)


# TODO: Should be moved to cartography.intel.aws.util.common
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
            logger.info(f"fetching page number {i}")
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
# https://github.com/cartography-cncf/cartography/issues/297
# https://github.com/cartography-cncf/cartography/issues/243
# https://github.com/cartography-cncf/cartography/issues/65
# https://github.com/cartography-cncf/cartography/issues/25


def backoff_handler(details: Dict) -> None:
    """
    Log backoff retry attempts for monitoring and debugging.

    This handler function is called by the backoff decorator when retries
    are being performed. It provides visibility into retry patterns and
    helps with debugging API rate limiting or connectivity issues.

    Args:
        details: Dictionary containing backoff information including:
                - wait: Number of seconds to wait before retry
                - tries: Number of attempts made so far
                - target: The function being retried

    Examples:
        The function is typically used automatically by backoff decorators:
        >>> @backoff.on_exception(
        ...     backoff.expo,
        ...     Exception,
        ...     on_backoff=backoff_handler
        ... )
        ... def api_call():
        ...     # Make API call that might fail
        ...     pass

    Note:
        This function logs at WARNING level to ensure visibility of retry
        operations in standard logging configurations. The message includes
        timing information and function identification for debugging.
        The backoff library may provide partial details (e.g. ``wait`` can be ``None`` when a retry is triggered immediately).
        Format the message defensively so logging never raises.
    """
    wait = details.get("wait")
    if isinstance(wait, (int, float)):
        wait_display = f"{wait:0.1f}"
    elif wait is None:
        wait_display = "unknown"
    else:
        wait_display = str(wait)

    tries = details.get("tries")
    tries_display = str(tries) if tries is not None else "unknown"

    target = details.get("target", "<unknown>")

    logger.warning(
        "Backing off %s seconds after %s tries. Calling function %s",
        wait_display,
        tries_display,
        target,
    )


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
]


# TODO Move this to cartography.intel.aws.util.common
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
              of resources. Should be a 'get_' function that queries AWS services.

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
    def inner_function(*args, **kwargs):  # type: ignore
        try:
            return func(*args, **kwargs)
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "InvalidToken":
                raise RuntimeError(
                    "AWS returned an InvalidToken error. Configure regional STS endpoints by "
                    "setting environment variable AWS_STS_REGIONAL_ENDPOINTS=regional or adding "
                    "'sts_regional_endpoints = regional' to your AWS config file."
                ) from e
            # The account is not authorized to use this service in this region
            # so we can continue without raising an exception
            if error_code in AWS_REGION_ACCESS_DENIED_ERROR_CODES:
                error_message = e.response.get("Error", {}).get("Message")
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

    return cast(AWSGetFunc, inner_function)


def retries_with_backoff(
    func: Callable,
    exception_type: Type[Exception],
    max_tries: int,
    on_backoff: Callable,
) -> Callable:
    """
    Add exponential backoff retry logic to any function.

    This decorator function wraps any callable with retry logic that uses
    exponential backoff. When the specified exception type is raised, the
    function will be retried with increasing delays between attempts until
    the maximum number of tries is reached.

    Args:
        func: The function to wrap with retry logic. Can be any callable.
        exception_type: The specific exception class that should trigger retries.
                       Only this exception type (and its subclasses) will be retried.
        max_tries: Maximum number of attempts before giving up. Includes the
                  initial attempt, so max_tries=3 means 1 initial + 2 retries.
        on_backoff: Callback function called before each retry attempt. Should
                   accept a dictionary with backoff details (wait, tries, target).

    Returns:
        The decorated function with retry logic applied. Preserves the original
        function's signature and return type.

    Examples:
        >>> import boto3
        >>> def get_s3_objects():
        ...     return s3_client.list_objects_v2(Bucket='my-bucket')
        >>>
        >>> resilient_s3_call = retries_with_backoff(
        ...     get_s3_objects,
        ...     botocore.exceptions.ClientError,
        ...     max_tries=4,
        ...     on_backoff=backoff_handler
        ... )

    Note:
        The function uses exponential backoff with jitter by default, meaning
        retry delays increase exponentially: ~1s, ~2s, ~4s, ~8s, etc. The
        exact timing may vary due to jitter to avoid thundering herd problems.

        Only the specified exception_type will trigger retries. Other exceptions
        will be raised immediately without retry attempts.

        The on_backoff callback receives a dictionary with keys:
        - 'wait': seconds to wait before next retry
        - 'tries': number of attempts made so far
        - 'target': the function being retried

        This is a general-purpose retry utility that can be applied to any
        function, not just AWS or API calls.
    """

    @wraps(func)
    @backoff.on_exception(
        backoff.expo,
        exception_type,
        max_tries=max_tries,
        on_backoff=on_backoff,
    )
    def inner_function(*args, **kwargs):  # type: ignore
        return func(*args, **kwargs)

    return cast(Callable, inner_function)


def dict_value_to_str(obj: Dict, key: str) -> Optional[str]:
    """
    Safely convert a dictionary value to string representation.

    This utility function retrieves a value from a dictionary and converts
    it to a string if it exists, or returns None if the key doesn't exist.
    This is useful for handling API responses where fields may be missing.

    Args:
        obj: The dictionary to search in.
        key: The key to look up in the dictionary.

    Returns:
        String representation of the value if key exists, None otherwise.
    """
    value = obj.get(key)
    if value is not None:
        return str(value)
    else:
        return None


# DEPRECATED: Use Neo4j datetime ingestion directly instead
def dict_date_to_epoch(obj: Dict, key: str) -> Optional[int]:
    """
    Convert a dictionary date value to Unix epoch timestamp.

    .. deprecated::
        This method is deprecated. Neo4j can handle datetime ingestion directly,
        and the datetime format should be preferred over epoch timestamps for
        better readability and native time operations support.

    This utility function retrieves a datetime object from a dictionary
    and converts it to a Unix epoch timestamp (seconds since 1970-01-01).
    This is useful for standardizing date representations in Neo4j.

    Args:
        obj: The dictionary containing the date value.
        key: The key to look up in the dictionary.

    Returns:
        Unix epoch timestamp as integer if key exists and contains a datetime,
        None otherwise.

    Examples:
        Converting datetime objects (deprecated approach):
        >>> from datetime import datetime
        >>> data = {
        ...     "created": datetime(2023, 1, 15, 10, 30, 0),
        ...     "modified": datetime(2023, 2, 20, 14, 45, 30)
        ... }
        >>> dict_date_to_epoch(data, "created")
        1673779800
        >>> dict_date_to_epoch(data, "modified")
        1676902530

    Note:
        The function expects the dictionary value to be a datetime object
        with a timestamp() method. This is commonly used when processing
        AWS API responses that return datetime objects for timestamps.

        Neo4j natively supports datetime objects and provides rich temporal
        functions for queries. Using datetime objects directly is preferred
        over epoch timestamps for better readability, timezone support, and
        access to Neo4j's temporal functions like date(), time(), and duration().

        For new code, consider storing datetime objects directly in Neo4j
        rather than converting them to epoch timestamps.
    """
    value = obj.get(key)
    if value is not None:
        return int(value.timestamp())
    else:
        return None


def camel_to_snake(name: str) -> str:
    """
    Convert CamelCase strings to snake_case format.

    This utility function converts CamelCase identifiers (commonly used in
    APIs) to snake_case format (commonly used in Python). It's useful for
    normalizing field names when processing API responses.

    Args:
        name: The CamelCase string to convert.

    Returns:
        The converted snake_case string.
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def batch(items: Iterable, size: int = DEFAULT_BATCH_SIZE) -> Iterable[List[Any]]:
    """
    Split an iterable into batches of specified size.

    This utility function takes any iterable and yields lists of items
    in batches of the specified size. This is useful for processing
    large datasets in manageable chunks, especially when working with
    APIs that have limits on batch operations.

    Args:
        items: The iterable to split into batches.
        size: The maximum size of each batch. Defaults to DEFAULT_BATCH_SIZE.

    Yields:
        Lists containing up to 'size' items from the original iterable.
        The last batch may contain fewer items if the total count is
        not evenly divisible by the batch size.

    Examples:
        Basic batching:
        >>> list(batch([1, 2, 3, 4, 5, 6, 7, 8], size=3))
        [[1, 2, 3], [4, 5, 6], [7, 8]]

    Note:
        The function uses itertools.islice for memory-efficient processing
        of large iterables. It doesn't load the entire iterable into memory
        at once, making it suitable for processing very large datasets.

        The DEFAULT_BATCH_SIZE is optimized for typical Neo4j operations
        but can be adjusted based on specific use cases and constraints.
    """
    it = iter(items)
    while chunk := list(islice(it, size)):
        yield chunk


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
    wrapped = backoff.on_exception(backoff.expo, CartographyThrottlingException)(
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
    return asyncio.get_event_loop().run_until_complete(asyncio.gather(*awaitables))


def to_datetime(value: Any) -> Union[datetime, None]:
    """
    Convert a neo4j.time.DateTime object to a Python datetime object.

    Neo4j returns datetime fields as neo4j.time.DateTime objects, which are not
    compatible with standard Python datetime or Pydantic datetime validation.
    This function converts neo4j.time.DateTime to Python datetime.

    :param value: A neo4j.time.DateTime object, Python datetime, or None
    :return: A Python datetime object or None
    :raises TypeError: If value is not a supported datetime type
    """
    if value is None:
        return None

    # Already a Python datetime
    if isinstance(value, datetime):
        return value

    # Handle neo4j.time.DateTime
    # neo4j.time.DateTime has a to_native() method that returns a Python datetime
    if hasattr(value, "to_native"):
        return cast(datetime, value.to_native())

    # Fallback: try to construct datetime from neo4j.time.DateTime attributes
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        tzinfo = getattr(value, "tzinfo", None) or timezone.utc
        return datetime(
            year=value.year,
            month=value.month,
            day=value.day,
            hour=getattr(value, "hour", 0),
            minute=getattr(value, "minute", 0),
            second=getattr(value, "second", 0),
            microsecond=(
                getattr(value, "nanosecond", 0) // 1000
                if hasattr(value, "nanosecond")
                else 0
            ),
            tzinfo=tzinfo,
        )

    raise TypeError(f"Cannot convert {type(value).__name__} to datetime")


def make_neo4j_datetime_validator() -> Callable[[Any], Union[datetime, None]]:
    """
    Create a Pydantic BeforeValidator for neo4j.time.DateTime conversion.

    Usage with Pydantic v2:
        from typing import Annotated
        from pydantic import BeforeValidator
        from cartography.util import to_datetime

        Neo4jDateTime = Annotated[datetime, BeforeValidator(to_datetime)]

        class MyModel(BaseModel):
            created_at: Neo4jDateTime

    Returns a lambda that can be used with BeforeValidator.
    """
    return lambda v: to_datetime(v)
