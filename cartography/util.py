import asyncio
import logging
import re
import sys
from functools import partial
from functools import wraps
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

from cartography.graph.job import GraphJob
from cartography.graph.statement import get_job_shortname
from cartography.stats import get_stats_client
from cartography.stats import ScopedStatsClient


if sys.version_info >= (3, 7):
    from importlib.resources import open_binary, read_text
else:
    from importlib_resources import open_binary, read_text

logger = logging.getLogger(__name__)


STATUS_SUCCESS = 0
STATUS_FAILURE = 1
STATUS_KEYBOARD_INTERRUPT = 130
DEFAULT_BATCH_SIZE = 1000


def run_analysis_job(
    filename: str,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
    package: str = 'cartography.data.jobs.analysis',
) -> None:
    """
    Enriches existing graph data with analysis jobs. This is designed for use with the sync stage
    cartography.intel.analysis.
    Runs the queries in the given Python `package` directory (cartography.data.jobs.analysis by default) for the given
    `filename`. All queries in this directory are intended to be run at the end of a full graph sync. As such, they are
    not scoped to a single sub resource. That is they will apply to _all_ AWS accounts/_all_ GCP projects/_all_ Okta
    organizations/etc.
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
    Runs analysis job only if the given set of resource dependencies was included in the requested_syncs.
    :param analysis_job_name: The name of the analysis job to run e.g. "aws_foreign_accounts.json"
    :param resource_dependencies: Set of resource sync names that must succeed in order to run the given analysis job.
    If there are no requirements, specify the empty set.
    :param requested_syncs: The value passed to cartography.config requested syncs as a set of strings.
    :param common_job_parameters: The common job params dict used in cartography.
    :param neo4j_session: The neo4j session object.
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
    package: str = 'cartography.data.jobs.scoped_analysis',
) -> None:
    """
    Enriches existing graph data scoped to a given sub resource - e.g. the current AWS account.
    Runs the queries in the cartography.data.jobs.scoped_analysis directory for the given `filename`. View the queries
    in cartography.data.jobs.scoped_analysis for specifics.
    """
    run_analysis_job(
        filename,
        neo4j_session,
        common_job_parameters,
        package,
    )


def run_cleanup_job(
    filename: str, neo4j_session: neo4j.Session, common_job_parameters: Dict,
    package: str = 'cartography.data.jobs.cleanup',
) -> None:
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
    '''
    This creates `ModuleSyncMetadata` nodes when called from each of the individual modules or sub-modules.
    The 'types' used here should be actual node labels. For example, if we did sync a particular AWSAccount's S3Buckets,
    the `grouptype` is 'AWSAccount', the `groupid` is the particular account's `id`, and the `syncedtype` is 'S3Bucket'.

    :param neo4j_session: Neo4j session object
    :param group_type: The parent module's type
    :param group_id: The parent module's id
    :param synced_type: The sub-module's type
    :param update_tag: Timestamp used to determine data freshness
    '''
    template = Template("""
        MERGE (n:ModuleSyncMetadata{id:'${group_type}_${group_id}_${synced_type}'})
        ON CREATE SET
            n:SyncMetadata, n.firstseen=timestamp()
        SET n.syncedtype='${synced_type}',
            n.grouptype='${group_type}',
            n.groupid='${group_id}',
            n.lastupdated=$UPDATE_TAG
    """)
    neo4j_session.run(
        template.safe_substitute(group_type=group_type, group_id=group_id, synced_type=synced_type),
        UPDATE_TAG=update_tag,
    )
    stat_handler.incr(f'{group_type}_{group_id}_{synced_type}_lastupdated', update_tag)


def load_resource_binary(package: str, resource_name: str) -> BinaryIO:
    return open_binary(package, resource_name)


R = TypeVar('R')
F = TypeVar('F', bound=Callable[..., Any])


def timeit(method: F) -> F:
    """
    This decorator uses statsd to time the execution of the wrapped method and sends it to the statsd server.
    This is only active if config.statsd_enabled is True.
    :param method: The function to measure execution
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


def aws_paginate(
    client: boto3.client,
    method_name: str,
    object_name: str,
    **kwargs: Any,
) -> List[Dict]:
    '''
    Helper method for boilerplate boto3 pagination
    The **kwargs will be forwarded to the paginator
    '''
    paginator = client.get_paginator(method_name)
    items = []
    i = 0
    for i, page in enumerate(paginator.paginate(**kwargs), start=1):
        if i % 100 == 0:
            logger.info(f'fetching page number {i}')
        if object_name in page:
            items.extend(page[object_name])
        else:
            logger.warning(
                f'''aws_paginate: Key "{object_name}" is not present, check if this is a typo.
If not, then the AWS datatype somehow does not have this key.''',
            )
    return items


AWSGetFunc = TypeVar('AWSGetFunc', bound=Callable[..., Iterable])

# fix for AWS TooManyRequestsException
# https://github.com/lyft/cartography/issues/297
# https://github.com/lyft/cartography/issues/243
# https://github.com/lyft/cartography/issues/65
# https://github.com/lyft/cartography/issues/25


def backoff_handler(details: Dict) -> None:
    """
    Handler that will be executed on exception by backoff mechanism
    """
    logger.warning("Backing off {wait:0.1f} seconds after {tries} tries. Calling function {target}".format(**details))


# TODO Move this to cartography.intel.aws.util.common
def aws_handle_regions(func: AWSGetFunc) -> AWSGetFunc:
    """
    A decorator for returning a default value on functions that would return a client error
     like AccessDenied for opt-in AWS regions, and other regions that might be disabled.

    The convenience of this decorator is that it auto-catches some of the potential
     Exceptions related to opt-in regions, and returns the specified `default_return_value`.

    This should be used on `get_` functions that normally return a list of items.
    """
    ERROR_CODES = [
        'AccessDenied',
        'AccessDeniedException',
        'AuthFailure',
        'InvalidClientTokenId',
        'UnauthorizedOperation',
        'UnrecognizedClientException',
        'InternalServerErrorException',
    ]

    @wraps(func)
    # fix for AWS TooManyRequestsException
    # https://github.com/lyft/cartography/issues/297
    # https://github.com/lyft/cartography/issues/243
    # https://github.com/lyft/cartography/issues/65
    # https://github.com/lyft/cartography/issues/25
    @backoff.on_exception(
        backoff.expo,
        botocore.exceptions.ClientError,
        max_time=600,
        on_backoff=backoff_handler,
    )
    def inner_function(*args, **kwargs):  # type: ignore
        try:
            return func(*args, **kwargs)
        except botocore.exceptions.ClientError as e:
            # The account is not authorized to use this service in this region
            # so we can continue without raising an exception
            if e.response['Error']['Code'] in ERROR_CODES:
                logger.warning("{} in this region. Skipping...".format(e.response['Error']['Message']))
                return []
            else:
                raise
    return cast(AWSGetFunc, inner_function)


def retries_with_backoff(
        func: Callable,
        exception_type: Type[Exception],
        max_tries: int,
        on_backoff: Callable,
) -> Callable:
    """
    Adds retry with backoff to the given function.  (Could expand the possible input parameters as needed.)
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
    Convert the value referenced by the key in the dict to a string, if it exists, and return it. If it doesn't exist,
    return None.
    """
    value = obj.get(key)
    if value is not None:
        return str(value)
    else:
        return None


def dict_date_to_epoch(obj: Dict, key: str) -> Optional[int]:
    """
    Convert the date referenced by the key in the dict to an epoch timestamp, if it exists, and return it. If it
    doesn't exist, return None.
    """
    value = obj.get(key)
    if value is not None:
        return int(value.timestamp())
    else:
        return None


def camel_to_snake(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def batch(items: Iterable, size: int = DEFAULT_BATCH_SIZE) -> List[List]:
    '''
    Takes an Iterable of items and returns a list of lists of the same items,
     batched into chunks of the provided `size`.

    Use:
    x = [1,2,3,4,5,6,7,8]
    batch(x, size=3) -> [[1, 2, 3], [4, 5, 6], [7, 8]]
    '''
    items = list(items)
    return [
        items[i: i + size]
        for i in range(0, len(items), size)
    ]


def is_throttling_exception(exc: Exception) -> bool:
    '''
    Returns True if the exception is caused by a client libraries throttling mechanism
    '''
    # https://boto3.amazonaws.com/v1/documentation/api/1.19.9/guide/error-handling.html
    if isinstance(exc, botocore.exceptions.ClientError):
        if exc.response['Error']['Code'] in ['LimitExceededException', 'Throttling']:
            return True
    # add other exceptions here, if needed, like:
    # https://cloud.google.com/python/docs/reference/storage/1.39.0/retry_timeout#configuring-retries
    # if isinstance(exc, google.api_core.exceptions.TooManyRequests):
    #     return True
    return False


def to_asynchronous(func: Callable[..., R], *args: Any, **kwargs: Any) -> Awaitable[R]:
    '''
    Returns a Future that will run a function and its arguments in the default threadpool.
    Helper until we start using python 3.9's asyncio.to_thread

    Calls are also wrapped within a backoff decorator to handle throttling errors.

    :param func: the function to be wrapped by the Future
    :param args: a series of arguments to be passed into func
    :param kwargs: a series of keyword arguments to be passed into func

    example:
    def my_func(arg1, arg2, kwarg1):
        return arg1 + arg2 + kwarg1

    # normal synchronous call:
    result = my_func(1, 2, kwarg1=3)

    # asynchronous call:
    future = to_asynchronous(my_func, 1, 2, kwarg1=3)

    # the result is stored in the future, and can be retrieved
    # from within another async function with:
    await future

    # or from within a synchronous function with our helper:
    to_synchronous(future)

    NOTE: to use this in a Jupyter notebook, you need to do:
    # import nest_asyncio
    # nest_asyncio.apply()
    '''
    CartographyThrottlingException = type('CartographyThrottlingException', (Exception,), {})

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if is_throttling_exception(exc):
                raise CartographyThrottlingException from exc
            raise

    # don't use @backoff as decorator, to preserve typing
    wrapped = backoff.on_exception(backoff.expo, CartographyThrottlingException)(wrapper)
    call = partial(wrapped, *args, **kwargs)
    return asyncio.get_event_loop().run_in_executor(None, call)


def to_synchronous(*awaitables: Awaitable[Any]) -> List[Any]:
    '''
    Synchronously waits for the Awaitable(s) to complete and returns their result(s).
    See https://docs.python.org/3.8/library/asyncio-task.html#asyncio-awaitables

    :param awaitables: a series of Awaitable objects, with each object being its own argument.
        i.e., not a single list of Awaitables

    example:
    async def my_async_func(my_arg):
        return my_arg

    async def another_async_func(my_arg2):
        return my_arg2

    remember that an invocation of an async function returns a Future (Awaitable),
    which needs to be awaited to get the result. You cannot await a Future from within
    a non-async function, so you could use this helper to get the result from a Future

    future_1 = my_async_func(1)
    future_2 = another_async_func(2)

    results = to_synchronous(future_1, future_2)
    '''
    return asyncio.get_event_loop().run_until_complete(asyncio.gather(*awaitables))
