import logging

import neo4j

from cartography.config import Config
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.users import sync
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_zoom_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not all(
        (config.zoom_account_id, config.zoom_client_id, config.zoom_client_secret)
    ):
        logger.info("Zoom import is not configured - skipping this module.")
        return

    client = ZoomClient(
        config.zoom_account_id, config.zoom_client_id, config.zoom_client_secret
    )
    with client.session:
        sync(neo4j_session, client, config.zoom_account_id, config.update_tag)
