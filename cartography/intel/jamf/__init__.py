import logging

import neo4j

from cartography.config import Config
from cartography.intel.jamf import computers
from cartography.intel.jamf import groups
from cartography.intel.jamf import mobile_devices
from cartography.intel.jamf.util import create_jamf_api_session
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_jamf_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    has_client = bool(config.jamf_client_id and config.jamf_client_secret)
    has_user = bool(config.jamf_user and config.jamf_password)
    if not config.jamf_base_uri or not (has_client or has_user):
        logger.info(
            "Jamf import is not configured - skipping this module. See docs to configure."
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": config.jamf_base_uri,
    }
    api_session = create_jamf_api_session(
        config.jamf_base_uri,
        jamf_user=config.jamf_user,
        jamf_password=config.jamf_password,
        jamf_client_id=config.jamf_client_id,
        jamf_client_secret=config.jamf_client_secret,
    )
    try:
        groups.sync(
            neo4j_session,
            api_session,
            config.jamf_base_uri,
            config.update_tag,
            common_job_parameters,
        )
        computers.sync(
            neo4j_session,
            api_session,
            config.jamf_base_uri,
            config.update_tag,
            common_job_parameters,
        )
        mobile_devices.sync(
            neo4j_session,
            api_session,
            config.jamf_base_uri,
            config.update_tag,
            common_job_parameters,
        )
    finally:
        api_session.close()
