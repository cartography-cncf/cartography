import logging
from typing import Optional

import neo4j

from cartography.config import Config
from cartography.intel.snipeit import asset
from cartography.intel.snipeit import user
from cartography.settings import check_module_settings
from cartography.settings import populate_settings_from_config
from cartography.settings import settings
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_snipeit_ingestion(neo4j_session: neo4j.Session, config: Optional[Config] = None) -> None:
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings('SnipeIT', ['base_url', 'token', 'tenant_id']):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
        "TENANT_ID": settings.snipeit.tenant_id,
    }

    # Ingest SnipeIT users and assets
    user.sync(neo4j_session, common_job_parameters, settings.snipeit.base_url, settings.snipeit.token)
    asset.sync(neo4j_session, common_job_parameters, settings.snipeit.base_url, settings.snipeit.token)
