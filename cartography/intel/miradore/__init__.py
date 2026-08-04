import logging

import neo4j

from cartography.config import Config
from cartography.intel.miradore import config_profiles
from cartography.intel.miradore import devices
from cartography.intel.miradore import locations
from cartography.intel.miradore import organizations
from cartography.intel.miradore import tags
from cartography.intel.miradore import users
from cartography.intel.miradore.util import create_miradore_api_session
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_BASE_URI = "https://online.miradore.com"


@timeit
def start_miradore_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:

    if not config.miradore_site_name or not config.miradore_api_key:
        logger.info(
            "Miradore import is not configured - skipping this module. See docs to configure."
        )
        return

    base_uri = config.miradore_base_uri or DEFAULT_BASE_URI
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": config.miradore_site_name,
    }
    api_session = create_miradore_api_session()
    # Devices are synced last: their relationships point at the organizations, locations,
    # tags, configuration profiles and users loaded by the earlier syncs.
    sync_args = (
        neo4j_session,
        api_session,
        base_uri,
        config.miradore_site_name,
        config.miradore_api_key,
        config.update_tag,
        common_job_parameters,
    )
    try:
        organizations.sync(*sync_args)
        locations.sync(*sync_args)
        tags.sync(*sync_args)
        config_profiles.sync(*sync_args)
        users.sync(*sync_args)
        devices.sync(*sync_args)
    finally:
        api_session.close()
