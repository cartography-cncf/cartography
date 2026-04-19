import logging

import neo4j

from cartography.config import Config
from cartography.intel.microsoft.entra import start_entra_ingestion
from cartography.intel.microsoft.intune import start_intune_ingestion
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_microsoft_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Perform ingestion of all Microsoft tenant data. Runs Entra first, then
    Intune, since Intune nodes relate back to Entra users, groups, and tenants.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if (
        not config.entra_tenant_id
        or not config.entra_client_id
        or not config.entra_client_secret
    ):
        logger.info(
            "Microsoft import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    start_entra_ingestion(neo4j_session, config)
    start_intune_ingestion(neo4j_session, config)
