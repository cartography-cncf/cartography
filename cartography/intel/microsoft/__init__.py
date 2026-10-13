import logging

import neo4j

from cartography.config import Config
from cartography.intel.microsoft.entra import start_entra_ingestion
from cartography.intel.microsoft.intune import start_intune_ingestion
from cartography.intel.microsoft.o365 import start_o365_ingestion
from cartography.intel.microsoft.util import requested_microsoft_syncs
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_microsoft_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Perform ingestion of Microsoft tenant data. Application authentication runs
    Entra, Intune, and O365; delegated authentication runs Entra only.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.microsoft_tenant_id or (
        not config.microsoft_delegated_auth
        and (not config.microsoft_client_id or not config.microsoft_client_secret)
    ):
        logger.info(
            "Microsoft import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    if config.microsoft_delegated_auth:
        logger.warning(
            "Microsoft delegated authentication is a best-effort Entra-only "
            "mode. Intune and O365 ingestion were not attempted. Prefer "
            "application authentication for complete inventory.",
        )
    requested = requested_microsoft_syncs(config)
    if requested is not None:
        logger.info(
            "Microsoft selective sync enabled for: %s", ", ".join(sorted(requested))
        )
    start_entra_ingestion(neo4j_session, config)
    if config.microsoft_delegated_auth:
        return
    if requested is None or "intune" in requested:
        start_intune_ingestion(neo4j_session, config)
    if requested is None or "o365" in requested:
        start_o365_ingestion(neo4j_session, config)
