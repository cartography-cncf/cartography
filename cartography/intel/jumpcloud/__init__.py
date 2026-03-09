import logging

import neo4j

import cartography.intel.jumpcloud.applications
import cartography.intel.jumpcloud.auth
import cartography.intel.jumpcloud.systems
import cartography.intel.jumpcloud.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_jumpcloud_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of JumpCloud data. Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.jumpcloud_api_key:
        logger.info(
            "JumpCloud import is not configured - skipping this module. "
            "Set jumpcloud_api_key (x-api-key auth).",
        )
        return

    if not config.jumpcloud_org_id:
        logger.error(
            "JumpCloud: jumpcloud_org_id is required but not set. "
            "Set --jumpcloud-org-id to enable proper sync.",
        )
        return

    auth_headers = cartography.intel.jumpcloud.auth.build_headers(
        api_key=config.jumpcloud_api_key,
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "ORG_ID": config.jumpcloud_org_id,
    }

    cartography.intel.jumpcloud.users.sync(
        neo4j_session,
        auth_headers,
        config.jumpcloud_org_id,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.jumpcloud.systems.sync(
        neo4j_session,
        auth_headers,
        config.jumpcloud_org_id,
        config.update_tag,
        common_job_parameters,
    )
    cartography.intel.jumpcloud.applications.sync(
        neo4j_session,
        auth_headers,
        config.jumpcloud_org_id,
        config.update_tag,
        common_job_parameters,
    )
