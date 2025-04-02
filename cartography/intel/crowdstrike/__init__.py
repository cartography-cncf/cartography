import logging

import neo4j

from cartography.config import Config
from cartography.settings import settings
from cartography.settings import check_module_settings
from cartography.intel.crowdstrike.endpoints import sync_hosts
from cartography.intel.crowdstrike.spotlight import sync_vulnerabilities
from cartography.intel.crowdstrike.util import get_authorization
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_crowdstrike_ingestion(
    neo4j_session: neo4j.Session, _: Config,
) -> None:
    """
    Perform ingestion of crowdstrike data.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object (DEPRECATED)
    :return: None
    """
    if not check_module_settings('Crowdstrike', ['client_id', 'client_secret'],):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
    }

    authorization = get_authorization(
        settings.crowdstrike.client_id,
        settings.crowdstrike.client_secret,
        settings.crowdstrike.get('api_url', None),
    )
    sync_hosts(
        neo4j_session,
        settings.common.update_tag,
        authorization,
    )
    sync_vulnerabilities(
        neo4j_session,
        settings.common.update_tag,
        authorization,
    )
    run_cleanup_job(
        "crowdstrike_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

    group_id = "public"
    if settings.crowdstrike.get('api_url', None):
        group_id = settings.crowdstrike.api_url
    merge_module_sync_metadata(
        neo4j_session,
        group_type='crowdstrike',
        group_id=group_id,
        synced_type='crowdstrike',
        update_tag=settings.common.update_tag,
        stat_handler=stat_handler,
    )
