import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.models.ubuntu.feed import UbuntuCVEFeedSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

FEED_ID = "ubuntu-security-cve-feed"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Syncing Ubuntu Security Feed node")
    feed_data = [
        {
            "id": FEED_ID,
            "name": "Ubuntu Security Feed",
            "url": f"{api_url}/security",
        },
    ]
    load(
        neo4j_session,
        UbuntuCVEFeedSchema(),
        feed_data,
        lastupdated=update_tag,
    )
