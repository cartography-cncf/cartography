import requests
from requests.adapters import HTTPAdapter
from urllib3.response import BaseHTTPResponse
from urllib3.util.retry import Retry

_RETRY_STATUS_CODES = (408, 429, 500, 502, 503, 504)
_MAX_RETRY_AFTER_SECONDS = 8


class _CappedRetry(Retry):
    def get_retry_after(self, response: BaseHTTPResponse) -> float | None:
        retry_after = super().get_retry_after(response)
        if retry_after is None:
            return None
        return min(retry_after, _MAX_RETRY_AFTER_SECONDS)


def _create_session(api_token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
        },
    )
    retry_policy = _CappedRetry(
        total=3,
        connect=3,
        read=3,
        status=3,
        other=0,
        allowed_methods=["GET"],
        status_forcelist=_RETRY_STATUS_CODES,
        backoff_factor=1,
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    return session
