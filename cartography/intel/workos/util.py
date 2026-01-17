import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import List

logger = logging.getLogger(__name__)


def paginated_list(list_func: Callable, **kwargs: Any) -> List[Dict[str, Any]]:
    """
    Helper to handle WorkOS cursor-based pagination.

    Args:
        list_func: The SDK list function to call
        **kwargs: Additional arguments for the list function

    Returns:
        List of all results across all pages
    """
    results = []
    after = None

    while True:
        # Call the list function with pagination parameters
        if after:
            response = list_func(after=after, **kwargs)
        else:
            response = list_func(**kwargs)

        # Add data from this page
        if hasattr(response, "data"):
            results.extend(response.data)
        else:
            # Handle case where response is already a list
            results.extend(response if isinstance(response, list) else [response])

        # Check if there's another page
        if not hasattr(response, "list_metadata"):
            break
        after = response.list_metadata.after
        if not after:
            break

    logger.info(f"Fetched {len(results)} items from WorkOS API")
    return results
