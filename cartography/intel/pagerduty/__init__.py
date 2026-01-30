import logging

import neo4j
from pdpyras import APISession

from cartography.config import Config
from cartography.intel.pagerduty.escalation_policies import sync_escalation_policies
from cartography.intel.pagerduty.schedules import sync_schedules
from cartography.intel.pagerduty.services import sync_services
from cartography.intel.pagerduty.teams import sync_teams
from cartography.intel.pagerduty.users import sync_users
from cartography.intel.pagerduty.vendors import sync_vendors
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_pagerduty_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Perform ingestion of pagerduty data.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if not config.pagerduty_api_key:
        logger.info(
            "PagerDuty import is not configured - skipping this module. See docs to configure.",
        )
        return
    session = APISession(config.pagerduty_api_key)
    if config.pagerduty_request_timeout is not None:
        session.timeout = config.pagerduty_request_timeout
    sync_users(neo4j_session, config.update_tag, session)
    sync_teams(neo4j_session, config.update_tag, session)
    sync_vendors(neo4j_session, config.update_tag, session)
    sync_services(neo4j_session, config.update_tag, session)
    sync_schedules(neo4j_session, config.update_tag, session)
    sync_escalation_policies(neo4j_session, config.update_tag, session)
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
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
