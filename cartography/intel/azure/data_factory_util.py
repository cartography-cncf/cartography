import logging
from collections.abc import Callable
from typing import TypeVar

import backoff
from azure.core.exceptions import HttpResponseError

from cartography.helpers import backoff_handler

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_MAX_TRIES = 3

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


def _is_retryable_data_factory_error(error: HttpResponseError) -> bool:
    status_code = _get_status_code(error)
    return status_code in _RETRYABLE_STATUS_CODES


def call_data_factory_operation(operation: str, func: Callable[[], T]) -> T:
    @backoff.on_exception(  # type: ignore[misc]
        backoff.expo,
        HttpResponseError,
        max_tries=_MAX_TRIES,
        giveup=lambda error: not _is_retryable_data_factory_error(error),
        on_backoff=backoff_handler,
        logger=None,
    )
    def _call() -> T:
        return func()

    try:
        return _call()
    except HttpResponseError as error:
        if not _is_retryable_data_factory_error(error):
            raise
        raise AzureDataFactoryTransientError(
            operation,
            _get_status_code(error),
        ) from error
