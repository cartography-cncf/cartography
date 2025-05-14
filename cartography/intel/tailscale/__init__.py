import logging

import neo4j
import requests

import cartography.intel.tailscale.devices
import cartography.intel.tailscale.postureintegrations
import cartography.intel.tailscale.tailnets
import cartography.intel.tailscale.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_tailscale_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Tailscale data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    # CHANGEME: Add here needed credentials
    if not config.tailscale_apikey:
        logger.info(
            "Tailscale import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    # Create requests sessions
    api_session = requests.session()

    # CHANGEME: Configure the authentication
    api_session.headers.update({"X-Api-Key": config.tailscale_apikey})

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": "https://api.tailscale.com/api/v2",
        "tailnet": config.tailscale_tailnet,
    }

    cartography.intel.tailscale.tailnets.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        tailnet=config.tailscale_tailnet,
    )

    cartography.intel.tailscale.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        tailnet=config.tailscale_tailnet,
    )

    cartography.intel.tailscale.devices.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        tailnet=config.tailscale_tailnet,
    )

    cartography.intel.tailscale.postureintegrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        tailnet=config.tailscale_tailnet,
    )
