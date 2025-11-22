import logging

import neo4j

from cartography.config import Config
from cartography.intel.konnect import certificates
from cartography.intel.konnect import control_planes
from cartography.intel.konnect import dp_client_certificates
from cartography.intel.konnect import dp_nodes
from cartography.intel.konnect import routes
from cartography.intel.konnect import services
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_konnect_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Starts the Kong Konnect ingestion process.
    
    :param neo4j_session: Neo4j session
    :param config: Config object
    :return: None
    """
    if not config.konnect_api_token:
        logger.info(
            "Kong Konnect import is not configured - skipping this module. "
            "To enable, set KONNECT_API_TOKEN environment variable or pass --konnect-api-token CLI argument.",
        )
        return

    # Set default API URL if not provided
    api_url = config.konnect_api_url or "https://us.api.konghq.com/v2"
    
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Sync control planes first
    control_planes.sync(
        neo4j_session,
        config.konnect_api_token,
        api_url,
        config.konnect_org_id,
        config.update_tag,
        common_job_parameters,
    )

    # Sync services for each control plane (before routes since routes reference services)
    services.sync(
        neo4j_session,
        config.konnect_api_token,
        api_url,
        config.update_tag,
        common_job_parameters,
    )

    # Sync routes for each control plane
    routes.sync(
        neo4j_session,
        config.konnect_api_token,
        api_url,
        config.update_tag,
        common_job_parameters,
    )

    # Sync DP nodes for each control plane
    dp_nodes.sync(
        neo4j_session,
        config.konnect_api_token,
        api_url,
        config.update_tag,
        common_job_parameters,
    )

    # Sync certificates for each control plane
    certificates.sync(
        neo4j_session,
        config.konnect_api_token,
        api_url,
        config.update_tag,
        common_job_parameters,
    )

    # Sync DP client certificates for each control plane
    dp_client_certificates.sync(
        neo4j_session,
        config.konnect_api_token,
        api_url,
        config.update_tag,
        common_job_parameters,
    )
