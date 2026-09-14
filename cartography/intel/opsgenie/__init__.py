import logging

import neo4j
import requests

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
    sync(
        neo4j_session,
        api_session,
        config.opsgenie_api_url.rstrip("/"),
        config.opsgenie_request_timeout,
        config.update_tag,
    )
