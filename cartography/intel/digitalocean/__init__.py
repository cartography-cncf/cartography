import logging

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_import

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
Manager = lazy_callable("digitalocean", "Manager")
compute = lazy_import("cartography.intel.digitalocean.compute")
management = lazy_import("cartography.intel.digitalocean.management")
platform = lazy_import("cartography.intel.digitalocean.platform")

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
    manager = Manager(token=config.digitalocean_token)

    account_id = platform.sync(
        neo4j_session, manager, config.update_tag, common_job_parameters
    )
    common_job_parameters["ACCOUNT_ID"] = str(account_id)
    projects_resources = management.sync(
        neo4j_session,
        manager,
        account_id,
        config.update_tag,
        common_job_parameters,
    )
    compute.sync(
        neo4j_session,
        manager,
        account_id,
        projects_resources,
        config.update_tag,
        common_job_parameters,
    )
