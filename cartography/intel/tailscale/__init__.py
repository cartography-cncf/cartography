import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.tailscale.acls
import cartography.intel.tailscale.devices
import cartography.intel.tailscale.grants
import cartography.intel.tailscale.postureintegrations
import cartography.intel.tailscale.postureresolution
import cartography.intel.tailscale.services
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

    if not config.tailscale_token or not config.tailscale_org:
        logger.info(
            "Tailscale import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    # Create requests sessions
    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": f"Bearer {config.tailscale_token}"})

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": config.tailscale_base_url,
        "org": config.tailscale_org,
    }

    cartography.intel.tailscale.tailnets.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=config.tailscale_org,
    )

    users = cartography.intel.tailscale.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=config.tailscale_org,
    )

    devices, device_posture_attributes = cartography.intel.tailscale.devices.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=config.tailscale_org,
    )

    cartography.intel.tailscale.postureintegrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=config.tailscale_org,
    )

    services = cartography.intel.tailscale.services.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org=config.tailscale_org,
    )

    postures, posture_conditions, grants, groups = (
        cartography.intel.tailscale.acls.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
            org=config.tailscale_org,
            users=users,
        )
    )

    posture_matches = cartography.intel.tailscale.postureresolution.sync(
        neo4j_session,
        org=config.tailscale_org,
        update_tag=config.update_tag,
        postures=postures,
        posture_conditions=posture_conditions,
        device_posture_attributes=device_posture_attributes,
    )

    cartography.intel.tailscale.grants.sync(
        neo4j_session,
        org=config.tailscale_org,
        update_tag=config.update_tag,
        grants=grants,
        devices=devices,
        groups=groups,
        tags=[],  # Tags are resolved from device data directly
        users=users,
        services=services,
        posture_matches=posture_matches,
    )
