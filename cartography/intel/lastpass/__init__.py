import logging

import neo4j

import cartography.intel.lastpass.users
from cartography.settings import check_module_settings
from cartography.settings import settings
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_lastpass_ingestion(neo4j_session: neo4j.Session) -> None:
    """
    If this module is configured, perform ingestion of Lastpass data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :return: None
    """
    if not check_module_settings('Lastpass', ['cid', 'provhash']):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
        "TENANT_ID": settings.lastpass.cid,
    }

    cartography.intel.lastpass.users.sync(
        neo4j_session,
        settings.lastpass.provhash,
        int(settings.lastpass.cid),
        settings.common.update_tag,
        common_job_parameters,
    )
