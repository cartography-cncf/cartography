import logging

import neo4j

from cartography.config import Config
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit
from cartography.util.lazy import lazy_callable

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
RestApiV2Client = lazy_callable("pagerduty", "RestApiV2Client")
sync_escalation_policies = lazy_callable(
    "cartography.intel.pagerduty.escalation_policies", "sync_escalation_policies"
)
sync_schedules = lazy_callable(
    "cartography.intel.pagerduty.schedules", "sync_schedules"
)
sync_services = lazy_callable("cartography.intel.pagerduty.services", "sync_services")
sync_teams = lazy_callable("cartography.intel.pagerduty.teams", "sync_teams")
sync_users = lazy_callable("cartography.intel.pagerduty.users", "sync_users")
sync_vendors = lazy_callable("cartography.intel.pagerduty.vendors", "sync_vendors")

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
    session = RestApiV2Client(config.pagerduty_api_key)
    if config.pagerduty_request_timeout is not None:
        session.timeout = config.pagerduty_request_timeout
    sync_users(neo4j_session, config.update_tag, session, common_job_parameters)
    sync_teams(neo4j_session, config.update_tag, session, common_job_parameters)
    sync_vendors(neo4j_session, config.update_tag, session, common_job_parameters)
    sync_services(neo4j_session, config.update_tag, session, common_job_parameters)
    sync_schedules(neo4j_session, config.update_tag, session, common_job_parameters)
    sync_escalation_policies(
        neo4j_session, config.update_tag, session, common_job_parameters
    )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="pagerduty",
        group_id="module",
        synced_type="pagerduty",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
