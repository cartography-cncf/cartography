import logging

import neo4j

from cartography.config import Config
from cartography.intel.jira.access import sync
from cartography.intel.jira.util import JiraClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_jira_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.jira_cloud_id or not config.jira_email or not config.jira_api_token:
        logger.info("Jira import is not configured - skipping this module.")
        return
    client = JiraClient(
        config.jira_cloud_id,
        config.jira_email,
        config.jira_api_token,
        config.jira_site_url,
    )
    try:
        sync(neo4j_session, client, config.update_tag)
    finally:
        client.session.close()
