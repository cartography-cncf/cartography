import logging

import neo4j
from cloudflare import Cloudflare

import cartography.intel.cloudflare.accounts
import cartography.intel.cloudflare.dnsrecords
import cartography.intel.cloudflare.members
import cartography.intel.cloudflare.roles
import cartography.intel.cloudflare.zones
from cartography.config import Config
from cartography.settings import check_module_settings
from cartography.settings import populate_settings_from_config
from cartography.settings import settings
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_cloudflare_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Cloudflare data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object (Deprecated: use settings instead)
    :return: None
    """
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings(
        "Cloudflare",
        [
            "token",
        ],
    ):
        return

    # Create client
    client = Cloudflare(api_token=settings.cloudflare.token)

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
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
