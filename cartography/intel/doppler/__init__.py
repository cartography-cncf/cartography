import logging

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import cartography.intel.doppler.configs
import cartography.intel.doppler.environments
import cartography.intel.doppler.groups
import cartography.intel.doppler.integrations
import cartography.intel.doppler.members
import cartography.intel.doppler.projects
import cartography.intel.doppler.roles
import cartography.intel.doppler.secrets
import cartography.intel.doppler.service_accounts
import cartography.intel.doppler.service_tokens
import cartography.intel.doppler.trusted_ips
import cartography.intel.doppler.users
import cartography.intel.doppler.webhooks
import cartography.intel.doppler.workplace
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_doppler_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Doppler data. Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.doppler_apikey:
        logger.info(
            "Doppler import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update(
        {
            "Authorization": f"Bearer {config.doppler_apikey}",
            "Accept": "application/json",
        }
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": "https://api.doppler.com/v3",
    }

    # The workplace is the tenant root; every other node hangs off it.
    workplace_id = cartography.intel.doppler.workplace.sync(
        neo4j_session, api_session, common_job_parameters
    )
    common_job_parameters["WORKPLACE_ID"] = workplace_id

    cartography.intel.doppler.roles.sync(
        neo4j_session, api_session, common_job_parameters
    )
    cartography.intel.doppler.users.sync(
        neo4j_session, api_session, common_job_parameters
    )
    cartography.intel.doppler.groups.sync(
        neo4j_session, api_session, common_job_parameters
    )
    cartography.intel.doppler.service_accounts.sync(
        neo4j_session, api_session, common_job_parameters
    )

    project_slugs = cartography.intel.doppler.projects.sync(
        neo4j_session, api_session, common_job_parameters
    )
    cartography.intel.doppler.environments.sync(
        neo4j_session, api_session, project_slugs, common_job_parameters
    )
    configs = cartography.intel.doppler.configs.sync(
        neo4j_session, api_session, project_slugs, common_job_parameters
    )

    # Per-config fan-out reusing the config list from configs.sync.
    cartography.intel.doppler.secrets.sync(
        neo4j_session, api_session, configs, common_job_parameters
    )
    cartography.intel.doppler.service_tokens.sync(
        neo4j_session, api_session, configs, common_job_parameters
    )
    cartography.intel.doppler.trusted_ips.sync(
        neo4j_session, api_session, configs, common_job_parameters
    )

    cartography.intel.doppler.integrations.sync(
        neo4j_session, api_session, common_job_parameters
    )
    cartography.intel.doppler.webhooks.sync(
        neo4j_session, api_session, project_slugs, common_job_parameters
    )

    # Project membership links the user/group/service-account nodes loaded above to
    # projects, so it must run last.
    cartography.intel.doppler.members.sync(
        neo4j_session, api_session, project_slugs, common_job_parameters
    )
