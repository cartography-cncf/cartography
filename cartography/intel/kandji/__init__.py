import logging
from typing import Optional

import neo4j

import cartography.intel.kandji.devices
from cartography.config import Config
from cartography.settings import populate_settings_from_config
from cartography.settings import check_module_settings
from cartography.settings import settings
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_kandji_ingestion(neo4j_session: neo4j.Session, config: Optional[Config]) -> None:
    """
    If this module is configured, perform ingestion of Kandji devices. Otherwise warn and exit

    :param neo4j_session: Neo4J session for database interface
    :param config: Configuration object for settings (Deprecated: use settings instead)

    :return: None
    """
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings('Kandji', ['base_uri', 'token', 'tenant_id']):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
        "TENANT_ID": settings.kandji.tenant_id,
    }

    cartography.intel.kandji.devices.sync(
        neo4j_session,
        settings.kandji.base_uri,
        settings.kandji.token,
        common_job_parameters=common_job_parameters,
    )
