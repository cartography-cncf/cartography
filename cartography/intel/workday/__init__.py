import logging

import neo4j

from cartography.config import Config
from cartography.intel.workday import people
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_workday_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Workday data. Otherwise warn and exit.

    :param neo4j_session: Neo4j session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not all(
        [
            config.workday_api_url,
            config.workday_api_login,
            config.workday_api_password,
        ],
    ):
        logger.info(
            "Workday import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    people.sync_workday_people(
        neo4j_session,
        config.workday_api_url,
        config.workday_api_login,
        config.workday_api_password,
        config.update_tag,
    )
