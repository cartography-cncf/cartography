import logging

import neo4j
from pydo import Client

from cartography.config import Config
from cartography.intel.digitalocean import compute
from cartography.intel.digitalocean import management
from cartography.intel.digitalocean import platform
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_digitalocean_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of DigitalOcean  data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    if not config.digitalocean_token:
        logger.info(
            "DigitalOcean import is not configured - skipping this module. See docs to configure.",
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    client = Client(token=config.digitalocean_token)

    account_id = platform.sync(
        neo4j_session, client, config.update_tag, common_job_parameters
    )
    if not account_id:
        logger.warning("No account ID found, skipping further DigitalOcean ingestion.")
        return

    common_job_parameters["ACCOUNT_ID"] = str(account_id)
    projects_resources = management.sync(
        neo4j_session,
        client,
        account_id,
        config.update_tag,
        common_job_parameters,
    )
    compute.sync(
        neo4j_session,
        client,
        account_id,
        projects_resources,
        config.update_tag,
        common_job_parameters,
    )
