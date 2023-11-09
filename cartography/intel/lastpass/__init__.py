import logging

import neo4j

import cartography.intel.lastpass.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_lastpass_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Lastpass data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if not config.lastpass_cid or not config.lastpass_provhash:
        logger.info(
            'Lastpass import is not configured - skipping this module. '
            'See docs to configure.',
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": config.lastpass_cid,
    }

    cartography.intel.lastpass.users.sync(
        neo4j_session,
        config.lastpass_provhash,
        int(config.lastpass_cid),
        config.update_tag,
        common_job_parameters,
    )
