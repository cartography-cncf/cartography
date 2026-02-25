import logging

import neo4j

import cartography.intel.ubuntu.cves
import cartography.intel.ubuntu.notices
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)

_DEFAULT_API_URL = "https://ubuntu.com"


@timeit
def start_ubuntu_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.ubuntu_security_enabled:
        logger.info(
            "Ubuntu Security import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_url = config.ubuntu_security_api_url or _DEFAULT_API_URL

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    cartography.intel.ubuntu.cves.sync(
        neo4j_session,
        api_url,
        config.update_tag,
        common_job_parameters,
    )

    cartography.intel.ubuntu.notices.sync(
        neo4j_session,
        api_url,
        config.update_tag,
        common_job_parameters,
    )
