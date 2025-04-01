import logging

import neo4j

from cartography.config import Config
from cartography.intel.snipeit import asset
from cartography.intel.snipeit import user
from cartography.settings import settings
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_snipeit_ingestion(neo4j_session: neo4j.Session, _: Config) -> None:
    if settings.snipeit.get('base_uri') is None or settings.snipeit.get('token') is None or settings.snipeit.get('tenant_id') is None:
        logger.warning(
            "Required parameter(s) missing. Skipping sync.",
        )
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
        "TENANT_ID": settings.snipeit.tenant_id,
    }

    # Ingest SnipeIT users and assets
    user.sync(neo4j_session, common_job_parameters, settings.snipeit.base_uri, settings.snipeit.token)
    asset.sync(neo4j_session, common_job_parameters, settings.snipeit.base_uri, settings.snipeit.token)
