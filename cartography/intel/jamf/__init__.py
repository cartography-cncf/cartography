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

    if not config.jamf_base_uri or not config.jamf_user or not config.jamf_password:
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
        config.jamf_user,
        config.jamf_password,
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
