import logging
from typing import Optional

import neo4j
from pdpyras import APISession

from cartography.config import Config
from cartography.intel.pagerduty.escalation_policies import sync_escalation_policies
from cartography.intel.pagerduty.schedules import sync_schedules
from cartography.intel.pagerduty.services import sync_services
from cartography.intel.pagerduty.teams import sync_teams
from cartography.intel.pagerduty.users import sync_users
from cartography.intel.pagerduty.vendors import sync_vendors
from cartography.settings import check_module_settings
from cartography.settings import populate_settings_from_config
from cartography.settings import settings
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_pagerduty_ingestion(
    neo4j_session: neo4j.Session, config: Optional[Config] = None
) -> None:
    """
    Perform ingestion of pagerduty data.
    :param neo4j_session: Neo4J session for database interface
    :param config: Configuration object (deprecated: use settings instead)
    :return: None
    """
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings("PagerDuty", ["api_key"]):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
    }

    session = APISession(settings.pagerduty.api_key)
    session.timeout = settings.common.http_timeout
    sync_users(neo4j_session, settings.common.update_tag, session)
    sync_teams(neo4j_session, settings.common.update_tag, session)
    sync_vendors(neo4j_session, settings.common.update_tag, session)
    sync_services(neo4j_session, settings.common.update_tag, session)
    sync_schedules(neo4j_session, settings.common.update_tag, session)
    sync_escalation_policies(neo4j_session, settings.common.update_tag, session)
    run_cleanup_job(
        "pagerduty_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="pagerduty",
        group_id="module",
        synced_type="pagerduty",
        update_tag=settings.common.update_tag,
        stat_handler=stat_handler,
    )
