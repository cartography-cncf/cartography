import logging

import neo4j
import requests

import cartography.intel.tailscale.acls
import cartography.intel.tailscale.devices
import cartography.intel.tailscale.postureintegrations
import cartography.intel.tailscale.tailnets
import cartography.intel.tailscale.users
from cartography.config import Config
from cartography.settings import check_module_settings
from cartography.settings import populate_settings_from_config
from cartography.settings import settings
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_tailscale_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Tailscale data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object (Deprecated: use settings instead)
    :return: None
    """

    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings("Tailscale", ["token", "org"]):
        return

    # Create requests sessions
    api_session = requests.session()
    api_session.headers.update({"Authorization": f"Bearer {settings.tailscale.token}"})

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
        "BASE_URL": settings.tailscale.get(
            "base_url", "https://api.tailscale.com/api/v2"
        ),
        "org": settings.tailscale.org,
    }

    cartography.intel.tailscale.tailnets.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=settings.tailscale.org,
    )

    users = cartography.intel.tailscale.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=settings.tailscale.org,
    )

    cartography.intel.tailscale.devices.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=settings.tailscale.org,
    )

    cartography.intel.tailscale.postureintegrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=settings.tailscale.org,
    )

    cartography.intel.tailscale.acls.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=settings.tailscale.org,
        users=users,
    )
