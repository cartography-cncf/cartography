import asyncio
import logging
from typing import Optional

import neo4j

from cartography.settings import settings, populate_settings_from_config, check_module_settings
from cartography.config import Config
from cartography.intel.entra.users import sync_entra_users
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_entra_ingestion(neo4j_session: neo4j.Session, config: Optional[Config] = None) -> None:
    """
    If this module is configured, perform ingestion of Entra data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object (DEPRECATED: use settings instead)
    :return: None
    """
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings('Entra', ['tenant_id', 'client_id', 'client_secret']):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
        "TENANT_ID": settings.entra.tenant_id,
    }

    asyncio.run(
        sync_entra_users(
            neo4j_session,
            settings.entra.tenant_id,
            settings.entra.client_id,
            settings.entra.client_secret,
            settings.common.update_tag,
            common_job_parameters,
        ),
    )
