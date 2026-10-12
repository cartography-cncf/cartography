import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from cartography.config import Config
from cartography.intel.opsgenie.resources import sync
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_opsgenie_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    if not config.opsgenie_api_key:
        logger.info(
            "Opsgenie import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = requests.Session()
    api_session.headers.update(
        {
            "Accept": "application/json",
            "Authorization": f"GenieKey {config.opsgenie_api_key}",
        },
    )
    # Opsgenie rate limits per API domain and answers 429 when exceeded. Every call
    # this module makes is an idempotent GET, so bounded retries are safe.
    api_session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=5,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
            ),
        ),
    )
    sync(
        neo4j_session,
        api_session,
        config.opsgenie_api_url.rstrip("/"),
        config.opsgenie_request_timeout,
        config.update_tag,
    )
