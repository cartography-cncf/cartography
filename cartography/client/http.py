from urllib3.response import BaseHTTPResponse
from urllib3.util.retry import Retry


class CappedRetry(Retry):
    """Limit each server-directed Retry-After delay to eight seconds.

    Retry counts and exponential backoff remain configured by each caller.
    Overriding the parser supports the project's urllib3 2.0 dependency floor.
    """

    def get_retry_after(self, response: BaseHTTPResponse) -> float | None:
        retry_after = super().get_retry_after(response)
        if retry_after is None:
            return None
        return min(retry_after, 8)
