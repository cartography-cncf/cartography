import logging
import requests

import neo4j

import cartography.intel.lastpass.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_cloudflare_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Cloudflare data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """

    # CHANGEME: Add here needed credentials
    if not config.cloudflare_apikey:
        logger.info(
            'Cloudflare import is not configured - skipping this module. '
            'See docs to configure.',
        )
        return

    # Create requests sessions
    api_session = requests.session()

    # CHANGEME: Configure the authentication
    api_session.headers.update(
        {'X-Api-Key': config.cloudflare_apikey}
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": "https://api.cloudflare.com/client/v4",
    }

    for account in cartography.intel.cloudflare.accounts.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    ):
        cartography.intel.cloudflare.roles.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
            account_id=account['id'],
        )
    
        cartography.intel.cloudflare.members.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
            account_id=account['id'],
        )
    

    for zone in cartography.intel.cloudflare.zones.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    ):
        cartography.intel.cloudflare.dnsrecords.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
            zone_id=zone['id'],
        )
    

