import logging

import neo4j

import cartography.intel.tenable.assets
import cartography.intel.tenable.findings
from cartography.config import Config
from cartography.intel.tenable.api import get_tenable_session
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

TENABLE_DEFAULT_URL = "https://cloud.tenable.com"


@timeit
def start_tenable_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Perform ingestion of Tenable data using the Export API.
    :param neo4j_session: Neo4j session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.tenable_access_key or not config.tenable_secret_key:
        logger.info(
            "Tenable import is not configured - skipping this module. "
            "Set tenable_access_key and tenable_secret_key to enable."
        )
        return

    if config.tenable_findings_lookback_days < 1:
        logger.warning(
            "Tenable findings lookback days is less than 1 - skipping this module. "
            "Set tenable_findings_lookback_days to a value greater than 0 to enable."
        )
        return

    base_url = config.tenable_url or TENABLE_DEFAULT_URL
    tenant_id = config.tenable_tenant_id or base_url.removeprefix(
        "https://"
    ).removeprefix("http://")

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENABLE_TENANT_ID": tenant_id,
    }

    session = get_tenable_session(config.tenable_access_key, config.tenable_secret_key)

    cartography.intel.tenable.assets.sync(
        neo4j_session,
        session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
    )

    cartography.intel.tenable.findings.sync(
        neo4j_session,
        session,
        base_url,
        tenant_id,
        config.update_tag,
        common_job_parameters,
        lookback_days=config.tenable_findings_lookback_days,
    )

    merge_module_sync_metadata(
        neo4j_session,
        group_type="TenableTenant",
        group_id=tenant_id,
        synced_type="TenableData",
        update_tag=config.update_tag,
        stat_handler=stat_handler,
    )
