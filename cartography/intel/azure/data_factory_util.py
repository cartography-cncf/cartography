import logging
import time
from collections.abc import Callable
from typing import TypeVar

from azure.core.exceptions import HttpResponseError

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = 2

T = TypeVar("T")


class AzureDataFactoryTransientError(Exception):
    def __init__(self, operation: str, status_code: int | None) -> None:
        self.operation = operation
        self.status_code = status_code
        super().__init__(
            "Transient Azure Data Factory API error during "
            f"{operation} (status_code={status_code})",
        )


def _get_status_code(error: HttpResponseError) -> int | None:
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        response = getattr(error, "response", None)
        status_code = getattr(response, "status_code", None)

    if status_code is None:
        return None

    try:
        return int(status_code)
    except (TypeError, ValueError):
        return None


def call_data_factory_operation(operation: str, func: Callable[[], T]) -> T:
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return func()
        except HttpResponseError as error:
            status_code = _get_status_code(error)
            if status_code not in _RETRYABLE_STATUS_CODES:
                raise

            if attempt == _MAX_ATTEMPTS:
                raise AzureDataFactoryTransientError(operation, status_code) from None

            logger.warning(
                "Transient Azure Data Factory API error during %s "
                "(status_code=%s). Retrying.",
                operation,
                status_code,
            )
            time.sleep(_RETRY_BACKOFF_SECONDS**attempt)

    raise RuntimeError("unreachable")
