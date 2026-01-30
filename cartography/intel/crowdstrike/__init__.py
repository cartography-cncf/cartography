import logging
from typing import Any

import neo4j

from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.crowdstrike.endpoints import sync_hosts
from cartography.intel.crowdstrike.spotlight import sync_vulnerabilities
from cartography.intel.crowdstrike.util import get_authorization
from cartography.models.crowdstrike.hosts import CrowdstrikeHostSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def start_crowdstrike_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Perform ingestion of crowdstrike data.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    if not config.crowdstrike_client_id or not config.crowdstrike_client_secret:
        logger.error("crowdstrike config not found")
        return

    authorization = get_authorization(
        config.crowdstrike_client_id,
        config.crowdstrike_client_secret,
        config.crowdstrike_api_url,
    )
    sync_hosts(
        neo4j_session,
        config.update_tag,
        authorization,
    )
    sync_vulnerabilities(
        neo4j_session,
        config.update_tag,
        authorization,
    )
    cleanup(neo4j_session, common_job_parameters)

    group_id = "public"
    if config.crowdstrike_api_url:
        group_id = config.crowdstrike_api_url
    merge_module_sync_metadata(
        neo4j_session,
        group_type="crowdstrike",
        group_id=group_id,
        synced_type="crowdstrike",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    logger.info("Running Crowdstrike cleanup")
    GraphJob.from_node_schema(CrowdstrikeHostSchema(), common_job_parameters).run(
        neo4j_session
    )

    # Cleanup other crowdstrike assets not handled by the data model
    run_cleanup_job(
        "crowdstrike_import_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )
