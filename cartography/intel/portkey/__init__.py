import logging

import neo4j

from cartography.config import Config
from cartography.intel.portkey import resources
from cartography.intel.portkey import users
from cartography.intel.portkey import util
from cartography.intel.portkey import workspaces
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_portkey_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.portkey_apikey or not config.portkey_org_id:
        logger.info(
            "Portkey import is not configured - skipping this module. See docs to configure.",
        )
        return

    api_session = util.create_api_session(config.portkey_apikey)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": config.portkey_base_url,
        "PORTKEY_ORG_ID": config.portkey_org_id,
    }

    users.sync(neo4j_session, api_session, common_job_parameters)
    workspace_data = workspaces.sync(neo4j_session, api_session, common_job_parameters)
    resources.sync_invites(neo4j_session, api_session, common_job_parameters)
    resources.sync_secret_references(neo4j_session, api_session, common_job_parameters)
    resources.sync_integrations(neo4j_session, api_session, common_job_parameters)
    resources.sync_mcp_integrations(neo4j_session, api_session, common_job_parameters)
    resources.sync_api_keys(neo4j_session, api_session, common_job_parameters)
    resources.sync_virtual_keys(neo4j_session, api_session, common_job_parameters)
    resources.sync_configs(neo4j_session, api_session, common_job_parameters)
    resources.sync_providers(
        neo4j_session,
        api_session,
        workspace_data,
        common_job_parameters,
    )
    resources.sync_mcp_servers(
        neo4j_session,
        api_session,
        workspace_data,
        common_job_parameters,
    )
    resources.sync_guardrails(neo4j_session, api_session, common_job_parameters)
    resources.sync_prompt_collections_and_prompts(
        neo4j_session,
        api_session,
        workspace_data,
        common_job_parameters,
    )
