import logging
from typing import Optional

import neo4j

import cartography.intel.lastpass.users
from cartography.config import Config
from cartography.settings import check_module_settings
from cartography.settings import populate_settings_from_config
from cartography.settings import settings
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_lastpass_ingestion(
    neo4j_session: neo4j.Session, config: Optional[Config] = None
) -> None:
    """
    If this module is configured, perform ingestion of Lastpass data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: Configuration object for settings (Deprecated: use settings instead)
    :return: None
    """
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings("Lastpass", ["cid", "provhash"]):
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
