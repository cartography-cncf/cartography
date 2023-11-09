import logging

import neo4j

from cartography.config import Config
from cartography.intel.bigfix.computers import sync
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_bigfix_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of BigFix data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if not config.bigfix_username or not config.bigfix_password:
        logger.info(
            'BigFix import is not configured - skipping this module. '
            'See docs to configure.',
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "ROOT_URL": config.bigfix_root_url,
    }
    sync(
        neo4j_session,
        config.bigfix_root_url,
        config.bigfix_username,
        config.bigfix_password,
        config.update_tag,
        common_job_parameters,
    )
