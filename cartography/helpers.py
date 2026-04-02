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

    Args:
        details: Dictionary containing backoff information including wait,
            tries, and target.
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
    """
    it = iter(items)
    while chunk := list(islice(it, size)):
        yield chunk
