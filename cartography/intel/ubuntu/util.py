from __future__ import annotations

import logging
from typing import Any

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from urllib3.exceptions import MaxRetryError

logger = logging.getLogger(__name__)


class LoggingRetry(Retry):
    """Retry subclass that logs each retry attempt for production observability."""

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
        remaining = self.total
        if isinstance(remaining, int):
            remaining -= 1
        logger.warning(
            "Ubuntu API retry: method=%s url=%s status=%s retries_left=%s error=%s",
            method,
            url,
            status,
            remaining,
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
    retry_policy = LoggingRetry(
        total=5,
        connect=1,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    return session
