from __future__ import annotations

import logging
from typing import Any

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from urllib3.exceptions import MaxRetryError

logger = logging.getLogger(__name__)

_UBUNTU_API_RETRY_TOTAL = 5
_UBUNTU_API_RETRY_CONNECT = 1
_UBUNTU_API_RETRY_BACKOFF_FACTOR = 1.0
_UBUNTU_API_STATUS_FORCELIST: tuple[int, ...] = (429, 500, 502, 503, 504)
_UBUNTU_API_ALLOWED_METHODS: frozenset[str] = frozenset({"GET"})


class LoggingRetry(Retry):
    """Retry subclass that logs each retry attempt for production observability."""

    def __init__(self, **kwargs: Any) -> None:
        # urllib3 reconstructs via type(self)(**params); accept full Retry kwargs.
        kwargs.setdefault("total", _UBUNTU_API_RETRY_TOTAL)
        kwargs.setdefault("connect", _UBUNTU_API_RETRY_CONNECT)
        kwargs.setdefault("backoff_factor", _UBUNTU_API_RETRY_BACKOFF_FACTOR)
        kwargs.setdefault("status_forcelist", _UBUNTU_API_STATUS_FORCELIST)
        kwargs.setdefault("allowed_methods", _UBUNTU_API_ALLOWED_METHODS)
        super().__init__(**kwargs)

    def increment(
        self,
        method: str | None = None,
        url: str | None = None,
        response: Any | None = None,
        error: Exception | None = None,
        _pool: Any | None = None,
        _stacktrace: Any = None,
    ) -> LoggingRetry:
        status = response.status if response else None
        retries_left: int | bool | None
        match self.total:
            case int(total_int):
                retries_left = total_int - 1
            case _:
                retries_left = self.total
        logger.warning(
            "Ubuntu API retry: method=%s url=%s status=%s retries_left=%s error=%s",
            method,
            url,
            status,
            retries_left,
            error,
        )
        try:
            return super().increment(
                method=method,
                url=url,
                response=response,
                error=error,
                _pool=_pool,
                _stacktrace=_stacktrace,
            )
        except MaxRetryError:
            logger.error(
                "Ubuntu API retries exhausted: method=%s url=%s last_status=%s",
                method,
                url,
                status,
            )
            raise


def retryable_session() -> Session:
    """Build a requests Session with automatic retries on transient HTTP errors.

    Covers 429 (rate-limit) and 5xx status codes that the Ubuntu Security API
    returns intermittently.  Uses exponential backoff via urllib3.
    """
    session = Session()
    retry_policy = LoggingRetry()
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    return session
