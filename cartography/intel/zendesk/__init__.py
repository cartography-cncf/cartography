import logging

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.zendesk import api_tokens
from cartography.intel.zendesk import users
from cartography.intel.zendesk.util import normalize_subdomain
from cartography.models.zendesk.tenant import ZendeskTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_zendesk_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.zendesk_subdomain or not config.zendesk_oauth_token:
        logger.info("Zendesk import is not configured - skipping this module.")
        return

    subdomain = normalize_subdomain(config.zendesk_subdomain)
    common_job_parameters = {"UPDATE_TAG": config.update_tag, "TENANT_ID": subdomain}
    logger.info("Starting Zendesk ingestion for %s", subdomain)
    with requests.Session() as session:
        session.headers.update(
            {"Authorization": f"Bearer {config.zendesk_oauth_token}"},
        )
        load(
            neo4j_session,
            ZendeskTenantSchema(),
            [{"id": subdomain, "domain": f"{subdomain}.zendesk.com"}],
            lastupdated=config.update_tag,
        )
        users.sync(
            neo4j_session,
            session,
            subdomain,
            config.update_tag,
            common_job_parameters,
        )
        api_tokens.sync(
            neo4j_session,
            session,
            subdomain,
            config.update_tag,
            common_job_parameters,
        )
    logger.info("Completed Zendesk ingestion for %s", subdomain)
