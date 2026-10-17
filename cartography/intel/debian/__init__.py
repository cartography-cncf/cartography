import logging

import neo4j
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.config import Config
from cartography.intel.debian import tracker
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _http_session() -> Session:
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


@timeit
def start_debian_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.debian_security_tracker_enabled:
        logger.info(
            "Debian security tracker import is not configured - skipping this "
            "module. See docs to configure.",
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "FEED_ID": tracker.FEED_ID,
    }
    with _http_session() as http_session:
        tracker.sync(
            neo4j_session,
            http_session,
            config.update_tag,
            common_job_parameters,
        )
