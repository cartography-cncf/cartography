import logging
from itertools import islice
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 1000


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
        The backoff library may provide partial details (e.g. ``wait`` can be
        ``None`` when a retry is triggered immediately). Format the message
        defensively so logging never raises.
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
