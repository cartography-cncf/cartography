import importlib
import logging
import re
import warnings
from datetime import datetime
from datetime import timezone
from functools import wraps
from importlib.resources import open_binary
from importlib.resources import read_text
from string import Template
from typing import Any
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
import neo4j

from cartography import helpers
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysisbuilder import to_graph_job
from cartography.graph.job import GraphJob
from cartography.graph.statement import get_job_shortname
from cartography.stats import get_stats_client
from cartography.stats import ScopedStatsClient

logger = logging.getLogger(__name__)


STATUS_SUCCESS = 0
STATUS_FAILURE = 1

# DEPRECATED: these used to live here and are part of the long-standing public API of
# cartography.util, so `from cartography.util import aws_handle_regions` keeps working
# for external modules and extensions. Remove in v1.0.0.
#
# They are resolved through the module __getattr__ below rather than re-exported with a
# plain import, because a plain import would pull boto3 into every cartography process
# again and undo the reason they were moved out.
_MOVED_TO_AWS = frozenset(
    {
        "AWSGetFunc",
        "AWS_REGION_ACCESS_DENIED_ERROR_CODES",
        "AWS_REGION_UNSUPPORTED_OPERATION_SNIPPETS",
        "DEFAULT_MAX_PAGES",
        "aws_handle_regions",
        "aws_paginate",
        "is_aws_region_skippable_client_error",
        "is_service_control_policy_explicit_deny",
        "is_throttling_exception",
        "to_asynchronous",
        "to_synchronous",
    },
)


def __getattr__(name: str) -> Any:
    if name in _MOVED_TO_AWS:
        warnings.warn(
            f"cartography.util.{name} moved to cartography.util.aws; import it from "
            f"there instead. This alias will be removed in v1.0.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(importlib.import_module("cartography.util.aws"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def backoff_handler(details: Dict) -> None:
    """
    Compatibility wrapper for cartography.helpers.backoff_handler.

    Internal callers should import this helper from cartography.helpers.
    This wrapper preserves the long-standing cartography.util API for
    external callers.
    """
    helpers.backoff_handler(details)


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


def run_typed_analysis_job(
    analysis_job: AnalysisJob,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    job = to_graph_job(analysis_job)
    job.merge_parameters(dict(common_job_parameters or {}))
    job.run(neo4j_session)


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


def run_typed_analysis_and_ensure_deps(
    analysis_job: AnalysisJob,
    resource_dependencies: Set[str],
    requested_syncs: Set[str],
    common_job_parameters: Dict[str, Any],
    neo4j_session: neo4j.Session,
) -> None:
    if not resource_dependencies.issubset(requested_syncs):
        logger.info(
            f"Did not run {analysis_job.name} because it needs {resource_dependencies} to be included "
            f"as a requested sync. You specified: {requested_syncs}. If you want this job to run, please change your "
            f"CLI args/cartography config so that all required resources are included.",
        )
        return

    run_typed_analysis_job(analysis_job, neo4j_session, common_job_parameters)


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
        filename: AnalysisJob object or name of the JSON file containing the scoped
                  analysis job queries.
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
        synced_type: The sub-module's node label that was synced (e.g., 'AWSS3Bucket').
        update_tag: Timestamp used to determine data freshness.
        stat_handler: StatsD client for sending metrics about the sync operation.

    Examples:
        Recording S3 bucket sync for an AWS account:
        >>> merge_module_sync_metadata(
        ...     neo4j_session,
        ...     group_type="AWSAccount",
        ...     group_id="123456789012",
        ...     synced_type="AWSS3Bucket",
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


def batch(
    items: Iterable,
    size: int = helpers.DEFAULT_BATCH_SIZE,
) -> Iterable[List[Any]]:
    """
    Compatibility wrapper for cartography.helpers.batch.

    Internal callers should import this helper from cartography.helpers.
    This wrapper preserves the long-standing cartography.util API for
    external callers.
    """
    return helpers.batch(items, size)


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


# DEPRECATED: `from cartography.util import *` exported the AWS helpers before they
# moved, and a star-import ignores the module __getattr__ above unless __all__ names
# them. Built from the module rather than written out, so the rest of the public
# surface stays exactly what a star-import gave before. Remove with _MOVED_TO_AWS in
# v1.0.0.
__all__ = sorted(
    [name for name in list(globals()) if not name.startswith("_")]
    + list(_MOVED_TO_AWS),
)
