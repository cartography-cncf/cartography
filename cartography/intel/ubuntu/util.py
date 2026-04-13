import logging

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)


def retryable_session() -> Session:
    """Build a requests Session with automatic retries on transient HTTP errors.

    Covers 429 (rate-limit) and 5xx status codes that the Ubuntu Security API
    returns intermittently.  Uses exponential backoff via urllib3.
    """
    session = Session()
    retry_policy = Retry(
        total=5,
        connect=1,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    return session
