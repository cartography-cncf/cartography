import requests
from requests.adapters import HTTPAdapter

from cartography.client.http import CappedRetry

_RETRY_STATUS_CODES = (408, 429, 500, 502, 503, 504)


def _create_session(api_token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
        },
    )
    retry_policy = CappedRetry(
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
