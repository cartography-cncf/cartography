import logging

import neo4j
from cloudflare import Cloudflare

import cartography.intel.cloudflare.accounts
import cartography.intel.cloudflare.dnsrecords
import cartography.intel.cloudflare.members
import cartography.intel.cloudflare.roles
import cartography.intel.cloudflare.zones
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

    if not config.cloudflare_token:
        logger.info(
            "Cloudflare import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    # Create client
    client = Cloudflare(api_token=config.cloudflare_token)

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    for account in cartography.intel.cloudflare.accounts.sync(
        neo4j_session,
        client,
        common_job_parameters,
    ):
        account_job_parameters = common_job_parameters.copy()
        account_job_parameters["account_id"] = account["id"]
        cartography.intel.cloudflare.roles.sync(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
        )

        cartography.intel.cloudflare.members.sync(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
        )

        for zone in cartography.intel.cloudflare.zones.sync(
            neo4j_session,
            client,
            account_job_parameters,
            account_id=account["id"],
        ):
            zone_job_parameters = account_job_parameters.copy()
            zone_job_parameters["zone_id"] = zone["id"]
            cartography.intel.cloudflare.dnsrecords.sync(
                neo4j_session,
                client,
                zone_job_parameters,
                zone_id=zone["id"],
            )
