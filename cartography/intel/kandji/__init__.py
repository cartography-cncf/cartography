import logging

import neo4j

import cartography.intel.kandji.devices
from cartography.settings import check_module_settings
from cartography.settings import settings
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_kandji_ingestion(neo4j_session: neo4j.Session) -> None:
    """
    If this module is configured, perform ingestion of Kandji devices. Otherwise warn and exit

    :param neo4j_session: Neo4J session for database interface

    :return: None
    """
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
